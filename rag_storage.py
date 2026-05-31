import os
import chromadb

class VideoRAGStore:
    def __init__(self, path="chroma_db_storage"):
        """
        Initializes the persistent ChromaDB client and gets or creates the transcripts collection.
        """
        if not os.path.exists(path):
            os.makedirs(path)
            
        self.client = chromadb.PersistentClient(path=path)
        # We use cosine similarity to calculate similarity/confidence scores
        self.collection = self.client.get_or_create_collection(
            name="video_transcripts_v2",
            metadata={"hnsw:space": "cosine"}
        )

    def add_transcript_chunks(self, video_id, video_title, chunks, embeddings, metadatas):
        """
        Adds text chunks, their pre-calculated embeddings, and metadata dictionaries to the collection.
        """
        ids = [f"{video_id}_chunk_{i}" for i in range(len(chunks))]
        
        # Enforce that every metadata dictionary contains video_id and video_title
        for meta in metadatas:
            meta["video_id"] = video_id
            meta["video_title"] = video_title
            
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks
        )

    def query(self, query_embedding, video_ids=None, top_k=5, chapter_filter=None):
        """
        Performs a semantic similarity search in ChromaDB.
        Returns a list of structured search result dicts with similarity scores, text, and metadata.
        """
        where_filter = {}
        if video_ids:
            if len(video_ids) == 1:
                where_filter["video_id"] = video_ids[0]
            else:
                where_filter["video_id"] = {"$in": video_ids}
                
        if chapter_filter:
            if where_filter:
                where_filter = {
                    "$and": [
                        where_filter,
                        {"chapter_name": chapter_filter}
                    ]
                }
            else:
                where_filter = {"chapter_name": chapter_filter}
                
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        # Format the output into a clean dictionary list
        formatted_results = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]
            # Chroma returns distances; for cosine space: similarity = 1.0 - distance
            distances = results["distances"][0] if "distances" in results else [0.5] * len(docs)
            
            for doc, meta, cid, dist in zip(docs, metas, ids, distances):
                # Normalize similarity score to percentage-like confidence score
                similarity = 1.0 - max(0.0, min(1.0, dist))
                confidence_score = int(similarity * 100)
                
                formatted_results.append({
                    "id": cid,
                    "text": doc,
                    "metadata": meta,
                    "confidence_score": confidence_score
                })
                
        return formatted_results

    def keyword_search(self, query_text, video_id=None):
        """
        Executes a case-insensitive keyword substring search across chunks.
        """
        where_filter = {"video_id": video_id} if video_id else None
        results = self.collection.get(
            where=where_filter,
            include=["documents", "metadatas"]
        )
        
        matches = []
        docs = results.get("documents", [])
        metas = results.get("metadatas", [])
        ids = results.get("ids", [])
        
        query_text_lower = query_text.lower()
        
        for doc, meta, cid in zip(docs, metas, ids):
            if query_text_lower in doc.lower():
                matches.append({
                    "id": cid,
                    "text": doc,
                    "metadata": meta,
                    # Fallback default score for exact matches
                    "confidence_score": 100
                })
        return matches

    def get_indexed_videos(self):
        """
        Scans all metadata in the collection and returns unique video titles and IDs.
        """
        results = self.collection.get(include=["metadatas"])
        metas = results.get("metadatas", [])
        
        videos = {}
        for meta in metas:
            vid = meta.get("video_id")
            title = meta.get("video_title", "Unknown Video")
            if vid:
                videos[vid] = title
                
        return [{"video_id": vid, "video_title": title} for vid, title in videos.items()]

    def delete_video(self, video_id):
        """
        Deletes all chunks associated with a specific video_id.
        """
        self.collection.delete(where={"video_id": video_id})
