# platform/ai/prompts/qwythos_poc.py

def get_qwythos_remediation_prompt(finding_title: str, root_cause: str, context: str) -> str:
    """Prompt khusus untuk Qwythos untuk merancang skrip validasi dan perbaikan."""
    
    return f"""Anda adalah 'Qwythos', AI Security Engineer spesialis eksploitasi dan remediasi.
Temuan berikut telah lolos tahap triase. Tugas Anda adalah memberikan langkah mitigasi dan ide skrip Proof-of-Concept (PoC) untuk memverifikasinya.

TEMUAN & AKAR MASALAH:
Title: {finding_title}
Root Cause: {root_cause}

KONTEKS KODE (RAG):
{context}

INSTRUKSI:
Anda WAJIB memberikan respons HANYA dalam format JSON yang valid tanpa markdown, tanpa penjelasan di luar JSON.
Struktur JSON yang wajib Anda gunakan:
{{
    "remediation_steps": [
        "langkah 1...",
        "langkah 2..."
    ],
    "verification_method": string, // Misalnya: "Kirim payload HTTP POST dengan karakter khusus ke endpoint /api/login"
    "poc_snippet": string // kode skrip Python/Bash untuk menguji celah ini (escape kutip ganda dengan benar)
}}
"""
