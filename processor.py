import os
import json
import traceback
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

def create_clickhouse_client():
    """Reads connection details from environment variables and creates a ClickHouse client."""
    config = {
        "host": os.getenv("CLICKHOUSE_HOST"),
        "port": int(os.getenv("CLICKHOUSE_PORT", "8123")),
        "user": os.getenv("CLICKHOUSE_USER"),
        "password": os.getenv("CLICKHOUSE_PASSWORD"),
        "database": os.getenv("CLICKHOUSE_DATABASE"),
        "secure": os.getenv("CLICKHOUSE_SECURE", "false").lower() == 'true'
    }
    if not all([config["host"], config["user"], config["password"]]):
        raise ValueError("Error: Missing essential ClickHouse environment variables.")
    
    print(f"Connecting to host: {config['host']}:{config['port']}...")
    client = clickhouse_connect.get_client(**config)
    client.ping()
    print("Successfully connected to ClickHouse.")
    return client

def generate_json_manifest_and_sql_files(
    manifest_filename="analysis_manifest.json",
    sql_directory="mortgage_sql_queries"
):
    """
    A DUAL-ACTION script:
    1. Reads the analysis documentation from ClickHouse and generates a JSON manifest.
    2. Dynamically creates a directory and populates it with the corresponding .sql files.
    """
    client = None
    try:
        client = create_clickhouse_client()
        
        # Query our documentation table, focusing on the mortgage dataset
        query = "SELECT * FROM default.view_metadata_catalog;"
        
        print("\nExecuting query to fetch analysis documentation for mortgage dataset...")
        result = client.query(query)
        
        if result.result_rows:
            docs_from_db = [dict(zip(result.column_names, row)) for row in result.result_rows]
            
            # --- ACTION 1: Generate the JSON Manifest ---
            print(f"\nFound {len(docs_from_db)} documented views. Generating JSON manifest...")
            final_manifest = docs_from_db
            
            with open(manifest_filename, 'w') as f:
                json.dump(final_manifest, f, indent=4)
            
            print(f"  - Success! Agent manifest saved to: {os.path.abspath(manifest_filename)}")
            # ---------------------------------------------
            
            # --- ACTION 2: Generate the SQL Files ---
            print(f"\nNow generating the '{sql_directory}' library...")
            
            # Ensure the target directory exists, creating it if it doesn't
            os.makedirs(sql_directory, exist_ok=True)
            
            files_created = 0
            for doc_item in docs_from_db:
                file_name = doc_item.get("sql_template_path")
                view_name = doc_item.get("view_name")
                
                if file_name and view_name:
                    file_path = os.path.join(sql_directory, file_name)
                    # The content is the simple, direct query to the specific view
                    file_content = f"SELECT * FROM default.{view_name};"
                    
                    with open(file_path, 'w') as f:
                        f.write(file_content)
                    files_created += 1
            
            print(f"  - Success! Created {files_created} .sql files in: {os.path.abspath(sql_directory)}")
            # -----------------------------------------
            
        else:
            print("No documentation was found in the 'analysis_view_documentation' table for the mortgage dataset.")

    except Exception as e:
        print("\n--- An error occurred during processing ---")
        print(traceback.format_exc())
        
    finally:
        if client:
            print("\nProcessing complete.")

if __name__ == "__main__":
    generate_json_manifest_and_sql_files()