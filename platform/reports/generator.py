import os
import structlog
from jinja2 import Environment, FileSystemLoader
from .models import SecurityReportData

logger = structlog.get_logger()

class ReportGenerator:
    def __init__(self, template_dir: str = "platform/reports/templates"):
        # Konfigurasi Jinja2 untuk memuat template dari folder
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_name = "report.md.j2"
        self.logger = logger.bind(service="report_generator")

    def generate_markdown(self, report_data: SecurityReportData, output_path: str) -> str:
        """
        Merender data temuan ke dalam format Markdown dan menyimpannya ke disk.
        """
        self.logger.info("generating_report", target_id=str(report_data.target_id))
        
        try:
            # 1. Muat Template
            template = self.env.get_template(self.template_name)
            
            # 2. Render Template dengan data Pydantic (diubah ke dict)
            markdown_content = template.render(**report_data.model_dump())
            
            # 3. Simpan ke File
            # Pastikan direktori output ada
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
            self.logger.info("report_generated_successfully", path=output_path)
            return output_path
            
        except Exception as e:
            self.logger.error("report_generation_failed", error=str(e))
            raise e
