# Notes-only index. Completions, routine definitions and account data are never indexed.
import os
from pathlib import Path
def _collection(user_id):
    try:
        import chromadb
        p=Path(os.getenv("CHROMA_DIR","instance/chroma")); p.mkdir(parents=True,exist_ok=True)
        return chromadb.PersistentClient(path=str(p)).get_or_create_collection(name=f"user_notes_{user_id}")
    except Exception: return None
def rebuild_notes_index(user_id,notes):
    c=_collection(user_id)
    if c is None: return {"indexed":0,"available":False}
    old=c.get()
    if old.get("ids"): c.delete(ids=old["ids"])
    ids=[str(n.id) for n in notes]
    docs=[f"{n.title}\nDate: {n.local_date}\n{n.content}" for n in notes]
    metas=[{"date":n.local_date,"title":n.title} for n in notes]
    if ids: c.add(ids=ids,documents=docs,metadatas=metas)
    return {"indexed":len(ids),"available":True}
def retrieve_notes(user_id,query,limit=4):
    c=_collection(user_id)
    if c is None or c.count()==0: return []
    r=c.query(query_texts=[query],n_results=min(limit,c.count()))
    return [{"text":d,"metadata":m} for d,m in zip(r.get("documents",[[]])[0],r.get("metadatas",[[]])[0])]
def answer_from_notes(user_id,query):
    matches=retrieve_notes(user_id,query)
    if not matches: return "I couldn't find matching content in your saved notes. Add relevant notes first."
    context="\n\n".join(x["text"] for x in matches)
    # LangChain prompt interface is prepared; no remote model is called by default.
    try:
        from langchain_core.prompts import ChatPromptTemplate
        ChatPromptTemplate.from_template("Answer only from these notes: {context}\nQuestion: {question}").format(context=context,question=query)
    except Exception: pass
    return "Relevant saved notes:\n\n"+context
