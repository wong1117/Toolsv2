from typing import List
import structlog

logger = structlog.get_logger()

class SemanticChunker:
    def __init__(self):
        self.logger = logger.bind(service="semantic_chunker")
        
    def chunk_architecture_doc(self, content: str, max_tokens: int = 500) -> List[str]:
        """Memecah dokumen teks berdasarkan paragraf."""
        self.logger.info("chunking_markdown_doc")
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_tokens:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def chunk_source_code(self, code_content: str, language: str) -> List[str]:
        """Memecah kode sumber tanpa merusak fungsi."""
        self.logger.info("chunking_source_code", language=language)
        
        chunks = []
        if language.lower() in ['python', 'solidity', 'javascript']:
            lines = code_content.split('\n')
            current_block = []
            
            for line in lines:
                if line.startswith("def ") or line.startswith("class ") or line.startswith("function ") or line.startswith("contract "):
                    if current_block:
                        chunks.append("\n".join(current_block))
                        current_block = []
                current_block.append(line)
                
            if current_block:
                chunks.append("\n".join(current_block))
        else:
            chunks = self.chunk_architecture_doc(code_content)
            
        return chunks
