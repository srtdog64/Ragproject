"""
Async Ingestion Service
Handles document ingestion in the background
"""
import logging
import asyncio
from typing import List, Dict, Any
from rag.core.types import Document
from rag.ingest.ingester import Ingester  # Correct import path
from server.tasks import TaskInfo, TaskStatus

logger = logging.getLogger(__name__)

async def async_ingest_documents(
    task_info: TaskInfo,
    documents: List[Dict[str, Any]],
    ingester: Ingester,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Asynchronously ingest documents with progress tracking
    
    Args:
        task_info: Task information object for progress updates
        documents: List of document dictionaries
        ingester: Ingester instance
        batch_size: Number of documents to process in each batch
        
    Returns:
        Ingestion result with statistics
    """
    total_docs = len(documents)
    task_info.total = total_docs
    task_info.metadata["batch_size"] = batch_size
    
    logger.info(f"Starting async ingestion of {total_docs} documents in task {task_info.id}")
    
    total_chunks = 0
    processed_docs = 0
    failed_docs = []
    
    try:
        # Process documents in batches
        for i in range(0, total_docs, batch_size):
            if task_info.status == TaskStatus.CANCELLED:
                logger.info(f"Task {task_info.id} was cancelled")
                break
                
            batch = documents[i:i + batch_size]
            batch_end = min(i + batch_size, total_docs)
            
            logger.info(f"Task {task_info.id}: Processing batch {i//batch_size + 1}: docs {i+1}-{batch_end}")
            
            # Convert dicts to Document objects
            doc_objects = []
            for doc_dict in batch:
                try:
                    doc = Document(
                        id=doc_dict.get("id", ""),
                        title=doc_dict.get("title", ""),
                        source=doc_dict.get("source", ""),
                        text=doc_dict.get("text", "")
                    )
                    doc_objects.append(doc)
                except Exception as e:
                    logger.error(f"Failed to create document: {e}")
                    failed_docs.append({
                        "id": doc_dict.get("id"),
                        "error": str(e)
                    })
                    continue
            
            if doc_objects:
                # Update progress - which document we're processing
                first_title = doc_objects[0].title if doc_objects[0].title else "Document"
                task_info.current_item = f"Processing: {first_title[:50]}..."
                logger.debug(f"Task {task_info.id}: Current item: {task_info.current_item}")
                
                # Ingest the batch
                try:
                    result = await ingester.ingest(doc_objects)
                    
                    if result.isOk():
                        chunks = result.getValue()
                        total_chunks += chunks
                        processed_docs += len(doc_objects)
                        logger.info(f"Task {task_info.id}: Ingested batch: {chunks} chunks from {len(doc_objects)} docs")
                    else:
                        error = str(result.getError())
                        logger.error(f"Task {task_info.id}: Batch ingestion failed: {error}")
                        for doc in doc_objects:
                            failed_docs.append({
                                "id": doc.id,
                                "error": error
                            })
                            
                except Exception as e:
                    logger.error(f"Task {task_info.id}: Exception during batch ingestion: {e}")
                    for doc in doc_objects:
                        failed_docs.append({
                            "id": doc.id,
                            "error": str(e)
                        })
            
            # Update progress
            task_info.progress = min(batch_end, total_docs)
            logger.info(f"Task {task_info.id}: Progress updated: {task_info.progress}/{task_info.total}")
            
            # Add small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Task {task_info.id}: Critical error during ingestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    
    # Prepare final result
    result = {
        "total_documents": total_docs,
        "processed_documents": processed_docs,
        "failed_documents": len(failed_docs),
        "total_chunks": total_chunks,
        "failed_details": failed_docs[:10] if failed_docs else []  # Limit failed details
    }
    
    logger.info(f"Task {task_info.id}: Async ingestion completed: {processed_docs}/{total_docs} docs, {total_chunks} chunks")
    
    return result

async def async_ingest_with_callback(
    task_info: TaskInfo,
    documents: List[Dict[str, Any]],
    ingester: Ingester,
    progress_callback = None,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Async ingest with optional progress callback
    
    Args:
        task_info: Task information
        documents: Documents to ingest
        ingester: Ingester instance
        progress_callback: Optional callback function(progress, total, current_item)
        batch_size: Batch size for processing
    """
    total_docs = len(documents)
    task_info.total = total_docs
    
    total_chunks = 0
    processed_docs = 0
    
    for i in range(0, total_docs, batch_size):
        if task_info.status == TaskStatus.CANCELLED:
            break
            
        batch = documents[i:i + batch_size]
        batch_end = min(i + batch_size, total_docs)
        
        # Convert and process batch
        doc_objects = []
        for doc_dict in batch:
            doc = Document(
                id=doc_dict.get("id", ""),
                title=doc_dict.get("title", ""),
                source=doc_dict.get("source", ""),
                text=doc_dict.get("text", "")
            )
            doc_objects.append(doc)
        
        # Update task info
        task_info.progress = batch_end
        task_info.current_item = f"Batch {i//batch_size + 1}"
        
        # Call progress callback if provided
        if progress_callback:
            await progress_callback(batch_end, total_docs, task_info.current_item)
        
        # Ingest batch
        result = await ingester.ingest(doc_objects)
        if result.isOk():
            total_chunks += result.getValue()
            processed_docs += len(doc_objects)
        
        await asyncio.sleep(0.05)  # Small delay
    
    return {
        "processed": processed_docs,
        "total": total_docs,
        "chunks": total_chunks
    }
