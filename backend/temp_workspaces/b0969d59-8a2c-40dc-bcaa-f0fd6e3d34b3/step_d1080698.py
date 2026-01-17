
import sys
import json
import os

try:
    # Ensure modules_repo is in path (handled by executor PYTHONPATH)
    from file_reader.source import FileReader
except ImportError as e:
    print(json.dumps({"error": f"Import failed: {e}" }))
    sys.exit(1)

if __name__ == "__main__":
    try:
        args = json.loads(sys.argv[1])
        processor = FileReader()
        # Run
        result = processor.run(**args) if isinstance(args, dict) else processor.run(args)
        print(json.dumps(result))
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
