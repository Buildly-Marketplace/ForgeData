#!/usr/bin/env python3
"""
Security Audit Tool
Scans codebase for hardcoded credentials and provides remediation suggestions
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Patterns to detect hardcoded credentials
PATTERNS = {
    'api_key': [
        r"api[_-]?key\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-]{20,})['\"]",
        r"apiKey\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-]{20,})['\"]",
    ],
    'token': [
        r"[_-]?token\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-\%]{20,})['\"]",
        r"bearer[_-]?token\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-\%]{20,})['\"]",
    ],
    'password': [
        r"password\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-@!#\$%\^&\*]{8,})['\"]",
        r"passwd\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-@!#\$%\^&\*]{8,})['\"]",
    ],
    'secret': [
        r"secret\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-]{20,})['\"]",
        r"client[_-]?secret\s*=\s*['\"](?!.*\$\{)([A-Za-z0-9_\-]{20,})['\"]",
    ],
}

# Directories to scan
SCAN_DIRS = ['automation', 'marketing', 'dashboard', 'scripts']

# Files to exclude
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.pyc',
    'examples/',
    'config_loader.py',
    'config_usage_examples.py',
    'security_audit.py',
]


class SecurityAuditor:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.findings: List[Dict] = []
    
    def should_scan(self, file_path: Path) -> bool:
        """Check if file should be scanned"""
        file_str = str(file_path)
        
        # Skip excluded patterns
        for pattern in EXCLUDE_PATTERNS:
            if pattern in file_str:
                return False
        
        # Only scan Python files
        return file_path.suffix == '.py'
    
    def scan_file(self, file_path: Path) -> List[Tuple[int, str, str, str]]:
        """Scan a single file for hardcoded credentials"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue
                
                # Check each pattern
                for cred_type, patterns in PATTERNS.items():
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            # Extract the matched credential (first group)
                            matched_value = match.group(1) if match.groups() else match.group(0)
                            findings.append((line_num, cred_type, line.strip(), matched_value))
        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        return findings
    
    def scan_directory(self, directory: Path):
        """Recursively scan directory for hardcoded credentials"""
        for item in directory.rglob('*.py'):
            if self.should_scan(item):
                file_findings = self.scan_file(item)
                if file_findings:
                    for line_num, cred_type, line, value in file_findings:
                        self.findings.append({
                            'file': str(item.relative_to(self.root_dir)),
                            'line': line_num,
                            'type': cred_type,
                            'code': line,
                            'value': value[:20] + '...' if len(value) > 20 else value
                        })
    
    def run_audit(self):
        """Run full security audit"""
        print("🔍 ForgeMarketing Security Audit")
        print("=" * 70)
        print(f"Scanning: {self.root_dir}")
        print(f"Directories: {', '.join(SCAN_DIRS)}")
        print("=" * 70)
        print()
        
        for scan_dir in SCAN_DIRS:
            dir_path = self.root_dir / scan_dir
            if dir_path.exists():
                print(f"Scanning {scan_dir}/...")
                self.scan_directory(dir_path)
        
        return self.findings
    
    def print_report(self):
        """Print audit report"""
        if not self.findings:
            print("✅ No hardcoded credentials found!")
            print()
            print("Your codebase appears to be secure.")
            return
        
        print(f"\n⚠️  Found {len(self.findings)} potential hardcoded credentials:\n")
        
        # Group by file
        by_file = {}
        for finding in self.findings:
            file_path = finding['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(finding)
        
        # Print grouped findings
        for file_path, findings in sorted(by_file.items()):
            print(f"📄 {file_path}")
            for finding in findings:
                print(f"   Line {finding['line']:4d} | {finding['type']:10s} | {finding['code'][:60]}")
            print()
        
        # Print remediation suggestions
        print("=" * 70)
        print("🔧 Remediation Steps:")
        print("=" * 70)
        print()
        
        for file_path, findings in sorted(by_file.items()):
            print(f"\n📝 File: {file_path}")
            print("-" * 70)
            
            # Determine which config loader method to use
            has_api_key = any(f['type'] == 'api_key' for f in findings)
            has_token = any(f['type'] == 'token' for f in findings)
            has_password = any(f['type'] == 'password' for f in findings)
            has_secret = any(f['type'] == 'secret' for f in findings)
            
            print("\n1. Add import at top of file:")
            print("   from config.config_loader import config_loader")
            print()
            
            print("2. Replace hardcoded credentials with:")
            
            if 'twitter' in file_path.lower() or has_token:
                print("""
   # For Twitter credentials
   creds = config_loader.get_twitter_credentials('buildly')
   bearer_token = creds.get('bearer_token', '')
   api_key = creds.get('api_key', '')
   api_secret = creds.get('api_secret', '')
""")
            
            if 'email' in file_path.lower() or 'smtp' in file_path.lower() or has_password:
                print("""
   # For email configuration
   email_config = config_loader.get_brand_email_config('buildly')
   if email_config:
       smtp_host = email_config.smtp_host
       smtp_port = email_config.smtp_port
       smtp_user = email_config.smtp_user
       smtp_password = email_config.smtp_password
""")
            
            if 'analytics' in file_path.lower() or 'google' in file_path.lower():
                print("""
   # For Google Analytics
   ga_creds = config_loader.get_google_analytics_credentials('buildly')
   api_key = ga_creds.get('api_key', '')
   property_id = ga_creds.get('property_id', '')
""")
            
            print("\n3. Remove hardcoded values")
            print()
        
        print("\n" + "=" * 70)
        print("📚 Documentation:")
        print("=" * 70)
        print("• Security Guide: devdocs/SECURITY_MIGRATION_GUIDE.md")
        print("• Code Examples: examples/config_usage_examples.py")
        print("• Operations Guide: ops/README.md")
        print()


def main():
    """Main entry point"""
    # Get project root (parent of ops directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run audit
    auditor = SecurityAuditor(project_root)
    auditor.run_audit()
    auditor.print_report()
    
    # Exit with error code if findings exist
    if auditor.findings:
        print("❌ Security audit failed - hardcoded credentials found")
        print("   Follow remediation steps above to fix issues")
        exit(1)
    else:
        print("✅ Security audit passed - no issues found")
        exit(0)


if __name__ == '__main__':
    main()
