from platform.parser.models import NormalizedFinding, ScannerMeta, TargetMeta, Location, FindingEvidence, Severity

class SemgrepAdapter:
    @staticmethod
    def parse(raw_data: dict, target_meta: dict) -> list[NormalizedFinding]:
        findings = []
        scan_id = target_meta.get("scan_id")
        
        for result in raw_data.get("results", []):
            try:
                finding = NormalizedFinding(
                    scan_id=scan_id,
                    scanner=ScannerMeta(
                        name="semgrep",
                        version=raw_data.get("version", "unknown"),
                        rule_id=result.get("check_id", "unknown")
                    ),
                    target=TargetMeta(
                        target_id=target_meta.get("target_id"),
                        repository_url=target_meta.get("repository_url", ""),
                        commit_hash=target_meta.get("commit_hash", "latest")
                    ),
                    title=result.get("check_name", "Semgrep Finding"),
                    severity=Severity[result.get("extra", {}).get("severity", "MEDIUM").upper()],
                    description=result.get("extra", {}).get("message", ""),
                    evidence=FindingEvidence(
                        location=Location(
                            file_path=result.get("path", ""),
                            line_start=result.get("start", {}).get("line", 0),
                            line_end=result.get("end", {}).get("line")
                        ),
                        code_snippet=result.get("extra", {}).get("lines", "")
                    )
                )
                findings.append(finding)
            except Exception as e:
                # Skip invalid findings agar tidak menghentikan seluruh proses
                continue
                
        return findings
