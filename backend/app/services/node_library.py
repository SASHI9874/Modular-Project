import time

class NodeLibrary:
    """
    The 'Standard Library' of nodes. 
    Each method matches the 'icon' or 'type' defined in your Frontend Sidebar.
    """

    @staticmethod
    def pdf_loader(inputs: dict):
        # In a real app, 'inputs' would contain a file path.
        # Here we simulate real processing.
        print("--- [Real Execution] Loading PDF ---")
        time.sleep(1) # Simulate work
        return {
            "text": "This is the raw text extracted from the PDF document. It contains important data about AI."
        }

    @staticmethod
    def gpt_4(inputs: dict):
        # FIX: The executor already extracted the specific value for us.
        # So 'context' is already the string we want.
        context = inputs.get('context', '')
        
        # If context is still a dict (edge case), try to extract text, otherwise cast to str
        if isinstance(context, dict):
            context = context.get('text', str(context))
            
        prompt = inputs.get('prompt', 'Summarize this')
        
        print(f"--- [Real Execution] Calling LLM with context: {str(context)[:30]}... ---")
        
        return {
            "response": f"GPT-4 Analysis: I received {len(str(context))} characters. Summary: The document discusses AI data."
        }

    @staticmethod
    def vector_db(inputs: dict):
        chunks = inputs.get('chunks', [])
        print(f"--- [Real Execution] Indexing {len(chunks)} items ---")
        return {
            "retriever": "VectorStoreIndex(id=1234)"
        }
    
    @staticmethod
    def custom_code(inputs: dict, code: str):
        """
        DANGEROUS: Executes raw python code strings.
        Only enable this if you trust the user (or sandbox it).
        """
        local_scope = {"inputs": inputs}
        exec(code, {}, local_scope)
        return local_scope.get("output")

# Helper to map frontend labels to functions
NODE_MAP = {
    "pdf_loader": NodeLibrary.pdf_loader,
    "gpt-4": NodeLibrary.gpt_4,
    "vector-db": NodeLibrary.vector_db
}