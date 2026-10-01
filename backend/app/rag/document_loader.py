import os
import re
from typing import List, Dict, Any, Optional
from app.core.logging_config import logger

class DocumentChunkDTO:
    def __init__(
        self,
        document_name: str,
        document_code: str,
        title: str,
        category: str,
        chunk_index: int,
        content: str,
        page_number: Optional[int] = None,
        access_scope: str = "PUBLIC_OPERATIONAL",
        allowed_roles: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ):
        self.document_name = document_name
        self.document_code = document_code
        self.title = title
        self.category = category
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.content = content
        self.access_scope = access_scope
        self.allowed_roles = allowed_roles or ["Driver", "Dispatcher", "Logistics Manager", "Admin", "Operations Team"]
        self.metadata = metadata or {}
        self.embedding = embedding

class DocumentDTO:
    def __init__(
        self,
        document_name: str,
        document_code: str,
        title: str,
        category: str,
        file_type: str,
        total_pages: int,
        chunks: List[DocumentChunkDTO],
        access_scope: str = "PUBLIC_OPERATIONAL",
        allowed_roles: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.document_name = document_name
        self.document_code = document_code
        self.title = title
        self.category = category
        self.file_type = file_type
        self.total_pages = total_pages
        self.chunks = chunks
        self.access_scope = access_scope
        self.allowed_roles = allowed_roles or ["Driver", "Dispatcher", "Logistics Manager", "Admin", "Operations Team"]
        self.metadata = metadata or {}


def extract_text_from_pdf(filepath: str) -> List[Dict[str, Any]]:
    """
    Extract readable text from PDF page-by-page.
    Returns list of dicts: [{"page_number": 1, "text": "..."}]
    """
    pages_data = []
    
    # 1. Try pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            clean_text = text.strip()
            if clean_text:
                pages_data.append({
                    "page_number": idx + 1,
                    "text": clean_text
                })
        if pages_data:
            return pages_data
    except Exception as e:
        logger.warning(f"[DocumentLoader] pypdf extraction issue on {filepath}: {e}. Trying pymupdf.")

    # 2. Try pymupdf / fitz fallback
    try:
        import pymupdf
        doc = pymupdf.open(filepath)
        for idx, page in enumerate(doc):
            text = page.get_text("text") or ""
            clean_text = text.strip()
            if clean_text:
                pages_data.append({
                    "page_number": idx + 1,
                    "text": clean_text
                })
        doc.close()
    except Exception as e:
        logger.error(f"[DocumentLoader] pymupdf extraction failed on {filepath}: {e}")

    return pages_data


def detect_document_category(filename: str, text: str) -> str:
    fn = filename.lower()
    first_few_lines = " ".join(text.split("\n")[:5]).lower()
    
    # Check filename first
    if "failed" in fn or "unavail" in fn:
        return "Exception Management"
    elif "driver" in fn or "safety" in fn or "hos" in fn:
        return "Driver Safety & Regulations"
    elif "vehicle" in fn or "loading" in fn or "fleet" in fn:
        return "Vehicle Guidelines"
    elif "cold" in fn or "reefer" in fn:
        return "Cold Chain Compliance"
    elif "detention" in fn or "demurrage" in fn:
        return "Billing & Accessorials"
    elif "hazmat" in fn or "chemical" in fn:
        return "HAZMAT Regulations"
    elif "delivery" in fn or "procedure" in fn:
        return "Operations"

    # Check title / first lines next
    if "failed delivery" in first_few_lines:
        return "Exception Management"
    elif "driver safety" in first_few_lines or "hours of service" in first_few_lines:
        return "Driver Safety & Regulations"
    elif "vehicle loading" in first_few_lines or "fleet vehicle" in first_few_lines:
        return "Vehicle Guidelines"
    elif "cold chain" in first_few_lines:
        return "Cold Chain Compliance"
    elif "detention" in first_few_lines:
        return "Billing & Accessorials"
    elif "hazmat" in first_few_lines:
        return "HAZMAT Regulations"

    return "Operations"



def detect_document_code_and_title(filename: str, text: str) -> (str, str):
    # Try finding title with SOP code like "# SOP-LOG-02: Failed Delivery Policy"
    sop_title_match = re.search(r"#?\s*(SOP-[A-Z0-9-]+):\s*([^\n\r]+)", text, re.IGNORECASE)
    if sop_title_match:
        doc_code = sop_title_match.group(1).upper()
        title = sop_title_match.group(2).strip("#* ")
        return doc_code, title

    # Try finding standalone SOP code in text
    code_match = re.search(r"\b(SOP-[A-Z0-9-]+)\b", text, re.IGNORECASE)
    if code_match:
        doc_code = code_match.group(1).upper()
    else:
        base_name = os.path.splitext(filename)[0]
        doc_code = "DOC-" + base_name.upper().replace("_", "-")[:15]

    # Look for first non-banner line
    lines = [l.strip("#* \r\n") for l in text.split("\n") if l.strip("#* \r\n")]
    for line in lines:
        if "OPERATIONAL POLICY DOCUMENT" in line.upper() or "CONFIDENTIAL" in line.upper():
            continue
        title = re.sub(r"^SOP-[A-Z0-9-]+:\s*", "", line, flags=re.IGNORECASE).strip()
        if title:
            if len(title) > 80:
                title = title[:77] + "..."
            return doc_code, title

    title = filename.replace("_", " ").replace("-", " ").title()
    return doc_code, title



def chunk_text(
    text: str,
    max_chunk_size: int = 750,
    overlap_size: int = 150
) -> List[str]:
    """
    Split text into meaningful overlapping chunks respecting paragraphs and sentences.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    if len(clean_text) <= max_chunk_size:
        return [clean_text]

    # First attempt splitting by double newline (paragraphs) or markdown headers
    paragraphs = re.split(r"(?:\n\s*\n|\n(?=##?\s+))", clean_text)
    chunks: List[str] = []
    current_chunk = ""

    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue

        if len(p_clean) > max_chunk_size:
            # Paragraph itself is too large, split by sentences
            sentences = re.split(r"(?<=[.!?])\s+", p_clean)
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                if len(current_chunk) + len(s_clean) + 1 <= max_chunk_size:
                    current_chunk = f"{current_chunk} {s_clean}".strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                        # Overlap: keep tail of current_chunk
                        tail = current_chunk[-overlap_size:] if len(current_chunk) > overlap_size else ""
                        current_chunk = f"{tail} {s_clean}".strip()
                    else:
                        chunks.append(s_clean[:max_chunk_size])
                        current_chunk = s_clean[max_chunk_size - overlap_size:]
        else:
            if len(current_chunk) + len(p_clean) + 2 <= max_chunk_size:
                current_chunk = f"{current_chunk}\n\n{p_clean}".strip() if current_chunk else p_clean
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    tail = current_chunk[-overlap_size:] if len(current_chunk) > overlap_size else ""
                    current_chunk = f"{tail}\n\n{p_clean}".strip()
                else:
                    current_chunk = p_clean

    if current_chunk and (not chunks or current_chunk != chunks[-1]):
        chunks.append(current_chunk)

    return chunks


def detect_document_access_policy(filename: str, category: str, text: str) -> (str, List[str]):
    fn = filename.lower()
    t_lower = text.lower()
    
    # 1. Admin-only policies
    if "admin" in fn or "security" in fn or "credential" in fn or "audit" in fn or "executive" in fn:
        return "ADMIN", ["Admin"]
        
    # 2. Manager-only / Manager + Admin policies (financials, billing, detention, demurrage, rates)
    if "detention" in fn or "demurrage" in fn or "billing" in fn or "cost" in fn or "contract" in fn or category == "Billing & Accessorials":
        return "MANAGER", ["Logistics Manager", "Admin"]
    if "manager" in fn or "supervisory" in fn or "margin" in fn:
        return "MANAGER", ["Logistics Manager", "Admin"]

    # 3. Dispatcher + Manager + Admin (vehicle policies, fleet loading, cold chain, hazmat regulations)
    if "vehicle" in fn or "loading" in fn or "cold" in fn or "reefer" in fn or "hazmat" in fn or category in ["Vehicle Guidelines", "Cold Chain Compliance", "HAZMAT Regulations"]:
        return "DISPATCHER", ["Dispatcher", "Logistics Manager", "Admin", "Operations Team"]

    # 4. Public Operational / Driver accessible (driver safety, HOS, delivery procedures, failed delivery policy)
    if "driver" in fn or "safety" in fn or "hos" in fn or "delivery" in fn or "failed" in fn or category in ["Driver Safety & Regulations", "Operations", "Exception Management"]:
        return "PUBLIC_OPERATIONAL", ["Driver", "Dispatcher", "Logistics Manager", "Admin", "Operations Team"]

    return "PUBLIC_OPERATIONAL", ["Driver", "Dispatcher", "Logistics Manager", "Admin", "Operations Team"]


def load_single_document(filepath: str) -> Optional[DocumentDTO]:
    """
    Process a single document (.pdf, .txt, .md) into a DocumentDTO with chunked metadata.
    """
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return None

    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".txt", ".md"]:
        logger.info(f"Skipping unsupported file format: {filename}")
        return None

    pages_data: List[Dict[str, Any]] = []

    if ext == ".pdf":
        pages_data = extract_text_from_pdf(filepath)
        file_type = "pdf"
    else:
        # TXT or MD
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                full_text = f.read()
            if full_text.strip():
                pages_data = [{"page_number": 1, "text": full_text.strip()}]
        except Exception as e:
            logger.error(f"Failed to read text file {filepath}: {e}")
            return None
        file_type = ext.replace(".", "")

    if not pages_data:
        logger.warning(f"Document {filename} is empty or unreadable.")
        return None

    full_document_text = "\n\n".join(p["text"] for p in pages_data)
    doc_code, title = detect_document_code_and_title(filename, full_document_text)
    category = detect_document_category(filename, full_document_text)
    access_scope, allowed_roles = detect_document_access_policy(filename, category, full_document_text)
    total_pages = len(pages_data)

    chunks: List[DocumentChunkDTO] = []
    chunk_index = 0

    for p_info in pages_data:
        p_num = p_info["page_number"]
        p_text = p_info["text"]
        p_chunks = chunk_text(p_text, max_chunk_size=750, overlap_size=120)

        for c_text in p_chunks:
            chunk = DocumentChunkDTO(
                document_name=filename,
                document_code=doc_code,
                title=f"{title} (P.{p_num})",
                category=category,
                chunk_index=chunk_index,
                page_number=p_num,
                content=c_text,
                access_scope=access_scope,
                allowed_roles=allowed_roles,
                metadata={
                    "filename": filename,
                    "file_type": file_type,
                    "doc_code": doc_code,
                    "doc_title": title,
                    "page_number": p_num,
                    "total_pages": total_pages,
                    "category": category,
                    "access_scope": access_scope,
                    "allowed_roles": allowed_roles
                }
            )
            chunks.append(chunk)
            chunk_index += 1

    doc_dto = DocumentDTO(
        document_name=filename,
        document_code=doc_code,
        title=title,
        category=category,
        file_type=file_type,
        total_pages=total_pages,
        chunks=chunks,
        access_scope=access_scope,
        allowed_roles=allowed_roles,
        metadata={
            "filename": filename,
            "file_type": file_type,
            "doc_code": doc_code,
            "title": title,
            "category": category,
            "access_scope": access_scope,
            "allowed_roles": allowed_roles,
            "total_pages": total_pages,
            "total_chunks": len(chunks)
        }
    )
    logger.info(f"Loaded document '{filename}' ({doc_code}) [{access_scope} -> {allowed_roles}] -> {len(chunks)} chunks across {total_pages} page(s).")
    return doc_dto


def load_documents_from_directory(directory_path: str) -> List[DocumentDTO]:
    """
    Scan directory for PDF, TXT, and MD files and parse into DocumentDTOs.
    """
    documents: List[DocumentDTO] = []
    if not os.path.exists(directory_path):
        logger.warning(f"Directory does not exist: {directory_path}")
        return documents

    for fname in sorted(os.listdir(directory_path)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in [".pdf", ".txt", ".md"]:
            fpath = os.path.join(directory_path, fname)
            doc_dto = load_single_document(fpath)
            if doc_dto:
                documents.append(doc_dto)

    logger.info(f"Loaded {len(documents)} document(s) from directory: {directory_path}")
    return documents
