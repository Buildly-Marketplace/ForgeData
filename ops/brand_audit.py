#!/usr/bin/env python3
"""
Brand Reference Audit Tool
Scans for hardcoded brand names that should be loaded from database
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Brand patterns to scan for (regex patterns)
# These should NOT appear hardcoded - brands should come from database
BRAND_PATTERNS = [
    r'\bbuildly\b',
    r'\bfoundry\b', 
    r'\bopenbuild\b',
    r'\bradical\b',
    r'\boregonsoftware\b'
]

# File patterns to exclude
EXCLUDE_PATTERNS = [
    'venv/', '.venv/', 'site-packages/', '__pycache__/', '.git/',
    'node_modules/', '.pytest_cache/', 'instance/', 'logs/',
    'email_audit_logs/', 'sent_emails_archive/', 'reports/',
    'archive/', 'ops/brand_audit.py', 'config/brand_loader.py',
    'devdocs/', 'docs/', 'examples/', '.yaml', 'config/brands.yaml',
    'BUILDLY.yaml', 'ops/helm/'
]

# Patterns that are OK (configuration, documentation, comments)
WHITELIST_PATTERNS = [
    r'#.*buildly',  # Comments
    r'""".*buildly.*"""',  # Docstrings
    r"'author'.*buildly",  # Metadata
    r'homepage.*buildly',  # URLs
    r'repository.*buildly',  # Git repos
    r'\.buildly\.io',  # Domain names
    r'@buildly',  # Twitter handles
    r'team@buildly\.io',  # Email addresses
    r'buildly/forgemark',  # Docker images
]


class BrandAudit:
    """Audit tool for hardcoded brand references"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.issues: List[Dict] = []
        
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scan"""
        path_str = str(file_path.relative_to(self.project_root))
        return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)
    
    def is_whitelisted(self, line: str, brand: str) -> bool:
        """Check if line matches whitelist patterns"""
        for pattern in WHITELIST_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for hardcoded brand references"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for brand_pattern in BRAND_PATTERNS:
                    # Extract brand name from pattern (e.g., r'\bbuildly\b' -> 'buildly')
                    brand_name = brand_pattern.replace(r'\b', '').replace('\\', '')
                    
                    # Look for brand name in quotes (hardcoded strings)
                    patterns = [
                        rf"['\"]({brand_name})['\"]",  # 'buildly' or "buildly"
                        rf"brands\s*=\s*\[.*{brand_name}.*\]",  # brands = ['buildly', ...]
                        rf"{brand_name}[_-]",  # buildly_ or buildly-
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            # Skip if whitelisted
                            if self.is_whitelisted(line, brand_name):
                                continue
                            
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'brand': brand_name,
                                'text': line.strip(),
                                'severity': self._determine_severity(file_path, line)
                            })
                            break  # Only report once per line
        
        except (UnicodeDecodeError, PermissionError):
            pass  # Skip binary files or files we can't read
        
        return issues
    
    def _determine_severity(self, file_path: Path, line: str) -> str:
        """Determine severity of the hardcoded reference"""
        path_str = str(file_path)
        
        # High severity: hardcoded lists that should use brand_loader
        if 'brands = [' in line or 'for brand in [' in line:
            return 'HIGH'
        
        # High severity: brand-specific configuration
        if re.search(r"['\"]buildly['\"]:\s*{", line):
            return 'HIGH'
        
        # Medium severity: conditional logic based on brand names
        if re.search(r"if.*==.*['\"](?:buildly|foundry|openbuild|radical|oregonsoftware)['\"]", line):
            return 'MEDIUM'
        
        # Medium severity: dictionary keys
        if re.search(r"\.get\(['\"](?:buildly|foundry|openbuild|radical|oregonsoftware)['\"]", line):
            return 'MEDIUM'
        
        # Low severity: default values, examples
        if 'default' in line.lower() or 'example' in line.lower():
            return 'LOW'
        
        return 'MEDIUM'
    
    def scan_all_files(self) -> None:
        """Scan all Python files in the project"""
        python_files = list(self.project_root.rglob('*.py'))
        
        print(f"🔍 Scanning {len(python_files)} Python files for hardcoded brand references...")
        print(f"   Note: All brands should be loaded from database, not hardcoded\n")
        
        for file_path in python_files:
            if self.should_skip_file(file_path):
                continue
            
            file_issues = self.scan_file(file_path)
            self.issues.extend(file_issues)
        
        # Group by file and severity
        self._print_results()
    
    def _print_results(self) -> None:
        """Print audit results grouped by severity and file"""
        if not self.issues:
            print("✅ No hardcoded brand references found!\n")
            return
        
        # Group by severity
        by_severity = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for issue in self.issues:
            by_severity[issue['severity']].append(issue)
        
        total_issues = len(self.issues)
        print(f"⚠️  Found {total_issues} hardcoded brand reference(s):\n")
        
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            issues = by_severity[severity]
            if not issues:
                continue
            
            print(f"\n{'='*80}")
            print(f"{severity} PRIORITY ({len(issues)} issues)")
            print('='*80)
            
            # Group by file
            by_file = {}
            for issue in issues:
                file = issue['file']
                if file not in by_file:
                    by_file[file] = []
                by_file[file].append(issue)
            
            for file, file_issues in sorted(by_file.items()):
                print(f"\n📄 {file}")
                for issue in file_issues:
                    print(f"   Line {issue['line']:4d}: {issue['text'][:80]}")
                    if issue['severity'] == 'HIGH':
                        print(f"              → Use: from config.brand_loader import get_all_brands")
                        print(f"                     brands = get_all_brands()")
        
        # Print summary and recommendations
        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print('='*80)
        print("""
1. HIGH Priority: Replace hardcoded brand lists with get_all_brands()
   
   Before:
     brands = ['buildly', 'foundry', 'openbuild', 'radical', 'oregonsoftware']
   
   After:
     from config.brand_loader import get_all_brands
     brands = get_all_brands()

2. MEDIUM Priority: Load brand configurations from database
   
   Before:
     if brand == 'buildly':
         config = BUILDLY_CONFIG
   
   After:
     from config.brand_loader import get_brand_details
     brand_data = get_brand_details(brand)

3. LOW Priority: Review default values and examples
   - These may be acceptable as fallbacks
   - Consider if they should be configurable

4. Run this tool regularly:
   python3 ops/brand_audit.py
        """)
        
        print(f"\n📊 Summary:")
        print(f"   Total files with issues: {len(set(i['file'] for i in self.issues))}")
        print(f"   HIGH priority issues: {len(by_severity['HIGH'])}")
        print(f"   MEDIUM priority issues: {len(by_severity['MEDIUM'])}")
        print(f"   LOW priority issues: {len(by_severity['LOW'])}")
        print()


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    auditor = BrandAudit(project_root)
    auditor.scan_all_files()
    
    # Exit with error code if high priority issues found
    high_priority = len([i for i in auditor.issues if i['severity'] == 'HIGH'])
    if high_priority > 0:
        exit(1)
    exit(0)


if __name__ == '__main__':
    main()
