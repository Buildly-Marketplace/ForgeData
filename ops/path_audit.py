#!/usr/bin/env python3
"""
Filesystem Path Audit Tool
Scans codebase for hardcoded absolute paths and provides remediation suggestions
"""

import os
import re
from pathlib import Path
from typing import List, Dict

# Patterns to detect hardcoded paths
PATH_PATTERNS = {
    'absolute_unix': r'/Users/[a-zA-Z0-9_/\-\.]+',
    'absolute_home': r'/home/[a-zA-Z0-9_/\-\.]+',
    'absolute_var': r'/var/[a-zA-Z0-9_/\-\.]+',
    'absolute_tmp': r'/tmp/[a-zA-Z0-9_/\-\.]+',
    'absolute_opt': r'/opt/[a-zA-Z0-9_/\-\.]+',
    'absolute_windows': r'[A-Z]:\\[\\\a-zA-Z0-9_\-\.]+',
}

# Directories to scan
SCAN_DIRS = ['automation', 'marketing', 'dashboard', 'scripts', 'config']

# Files to exclude
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.pyc',
    'path_audit.py',
    'examples/',
    'venv/',
    '.venv/',
    'site-packages/',
]


class PathAuditor:
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
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """Scan a single file for hardcoded paths"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                
                # Check each pattern
                for path_type, pattern in PATH_PATTERNS.items():
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # Skip if it's in a comment
                        if '#' in line and line.index('#') < line.index(match):
                            continue
                        
                        findings.append({
                            'file': str(file_path.relative_to(self.root_dir)),
                            'line': line_num,
                            'type': path_type,
                            'path': match,
                            'code': line.strip(),
                        })
        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        return findings
    
    def scan_directory(self, directory: Path):
        """Recursively scan directory for hardcoded paths"""
        for item in directory.rglob('*.py'):
            if self.should_scan(item):
                file_findings = self.scan_file(item)
                self.findings.extend(file_findings)
    
    def run_audit(self):
        """Run full path audit"""
        print("🔍 ForgeMarketing Filesystem Path Audit")
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
            print("✅ No hardcoded absolute paths found!")
            print()
            print("All filesystem references appear to be relative or configurable.")
            return
        
        print(f"\n⚠️  Found {len(self.findings)} hardcoded absolute paths:\n")
        
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
                print(f"   Line {finding['line']:4d} | {finding['type']:20s} | {finding['path']}")
            print()
        
        # Print remediation guide
        print("=" * 70)
        print("🔧 Remediation Guide:")
        print("=" * 70)
        print()
        
        print("Replace hardcoded absolute paths with relative paths:")
        print()
        print("1. Use project-relative paths:")
        print("   ❌ path = '/Users/user/Projects/app/data/file.db'")
        print("   ✅ project_root = Path(__file__).parent.parent")
        print("   ✅ path = project_root / 'data' / 'file.db'")
        print()
        
        print("2. Use environment variables for configurable paths:")
        print("   ❌ workspace = '/Users/user/Projects/workspace'")
        print("   ✅ workspace = os.getenv('WORKSPACE_ROOT', str(Path(__file__).parent.parent))")
        print()
        
        print("3. Accept path as constructor parameter:")
        print("   ❌ def __init__(self):")
        print("       self.db = '/Users/user/data.db'")
        print("   ✅ def __init__(self, db_path=None):")
        print("       project_root = Path(__file__).parent.parent")
        print("       self.db = db_path or project_root / 'data' / 'data.db'")
        print()
        
        print("4. For cross-platform compatibility:")
        print("   ✅ from pathlib import Path  # Use Path objects")
        print("   ✅ Path.home() / 'config'     # User home directory")
        print("   ✅ Path.cwd() / 'data'        # Current working directory")
        print()
        
        # Specific recommendations by file
        print("=" * 70)
        print("📝 File-Specific Recommendations:")
        print("=" * 70)
        print()
        
        for file_path, findings in sorted(by_file.items()):
            print(f"\n{file_path}:")
            print("-" * 70)
            
            # Identify the type of hardcoded path
            has_db_path = any('db' in f['path'].lower() or 'database' in f['path'].lower() for f in findings)
            has_workspace = any('workspace' in f['path'].lower() or 'Projects' in f['path'] for f in findings)
            
            if has_db_path:
                print("""
• Replace hardcoded database path:
  
  def __init__(self, db_path=None):
      project_root = Path(__file__).parent.parent
      default_db = project_root / 'data' / 'database.db'
      self.db_path = db_path or os.getenv('DATABASE_PATH', str(default_db))
""")
            
            if has_workspace:
                print("""
• Replace hardcoded workspace path:
  
  def __init__(self, workspace_root=None):
      if workspace_root:
          self.workspace_root = Path(workspace_root)
      elif os.getenv('WORKSPACE_ROOT'):
          self.workspace_root = Path(os.getenv('WORKSPACE_ROOT'))
      else:
          self.workspace_root = Path(__file__).parent.parent
""")
        
        print("\n" + "=" * 70)
        print("📚 Documentation:")
        print("=" * 70)
        print("• Path Best Practices: devdocs/PATH_GUIDELINES.md (create this)")
        print("• Configuration Guide: devdocs/SECURITY_MIGRATION_GUIDE.md")
        print()


def main():
    """Main entry point"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run audit
    auditor = PathAuditor(project_root)
    auditor.run_audit()
    auditor.print_report()
    
    # Exit with error code if findings exist
    if auditor.findings:
        print("❌ Path audit failed - hardcoded absolute paths found")
        print("   Follow remediation guide above to fix issues")
        exit(1)
    else:
        print("✅ Path audit passed - no hardcoded paths found")
        exit(0)


if __name__ == '__main__':
    main()
