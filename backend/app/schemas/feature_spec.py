from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Literal, Any
from enum import Enum

# --- 1. CONFIGURATION (Env Vars) ---
class FeatureConfigField(BaseModel):
    type: Literal["string", "number", "boolean"]
    required: bool = True
    description: Optional[str] = None
    default: Optional[Any] = None

class FeatureConfig(BaseModel):
    env: Dict[str, FeatureConfigField] = {}

# --- 2. UI METADATA (Sidebar Info) ---
class FeatureUI(BaseModel):
    icon: Optional[str] = "box"       # Lucide icon name
    color: Optional[str] = "#6366f1"  # Hex color
    category: Optional[str] = "General"
    label: Optional[str] = None       # Human readable name
    placement: Literal["sidebar", "main", "hidden"] = "main"

# --- 3. EXECUTION LIMITS (Safety) ---
class FeatureLimits(BaseModel):
    timeout_seconds: int = 30
    memory_mb: int = 512

# --- 4. STORAGE (Infrastructure) ---
class FeatureStorage(BaseModel):
    tables: List[str] = []
    vector_store: bool = False

# --- 5. API DEFINITION (For Client Generation) ---
class ApiMethod(BaseModel):
    name: str              # e.g. "upload"
    verb: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    path: str              # e.g. "/upload" (relative to feature root)
    has_file: bool = False # If true, we send FormData
    description: Optional[str] = None

class FeatureApi(BaseModel):
    methods: List[ApiMethod] = []

# --- 6. CONNECTION TYPES (NEW - FOR AGENTS) ---
class ConnectionType(str, Enum):
    """Types of connections between nodes"""
    DATA = "data"           # Normal data flow
    TOOL = "tool"           # Tool availability for agents
    MEMORY = "memory"       # Memory/context passing
    CONDITIONAL = "conditional"  # If/else branches (future)

class ConnectionMetadata:
    """Metadata for a connection"""
    def __init__(
        self,
        connection_type: ConnectionType,
        label: str = None,
        required: bool = False,
        multiple: bool = False
    ):
        self.connection_type = connection_type
        self.label = label
        self.required = required
        self.multiple = multiple

class ConnectionSpec(BaseModel):
    """Defines special connection requirements for agents"""
    type: str  # "tool", "memory", etc.
    multiple: bool = False
    required: bool = False
    description: Optional[str] = None
    
    @validator('type')
    def validate_connection_type(cls, v):
        valid_types = ['tool', 'memory', 'conditional', 'action', 'storage']
        if v not in valid_types:
            raise ValueError(f'Invalid connection type: {v}. Must be one of {valid_types}')
        return v

# --- 7. TOOL DEFINITION (NEW - FOR AGENT TOOLS) ---
class ToolParameter(BaseModel):
    """Parameter definition for a tool"""
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None  # For enumerated values

class ToolDefinition(BaseModel):
    """
    Defines a feature as a tool that can be used by agents.
    This allows agents to discover and call this feature.
    """
    name: str
    description: str  # Natural language description for LLM
    parameters: Dict[str, ToolParameter]
    returns: Dict[str, Any]  # Return type schema
    
    # Examples to help LLM understand usage
    examples: Optional[List[Dict[str, Any]]] = None

# --- UPDATED CLASSIFICATION (WITH NEW TYPES) ---
class FeatureClassification(BaseModel):
    capability: Literal[
        "input",      # Takes external data (Document Upload, API Input)
        "processor",  # Transforms data (Text Splitter, Embeddings)
        "storage",    # Stores data (Vector DB, Database)
        "action",     # Performs actions (LLM, API Call)
        "trigger",    # Entry points (Chat Input, Webhook)
        "agent",      # Agent orchestrators (ReAct Agent)
        "tool"        # Tools for agents (Calculator, Search)
    ]
    execution_model: Literal["sync", "async", "background"]
    state_scope: Literal["transient", "session", "persistent"]

class FeatureInfrastructure(BaseModel):
    system_dependencies: List[str] = []
    
class DataField(BaseModel):
    type: str
    description: Optional[str] = None
    optional: bool = False  # NEW: Mark optional fields

# --- UPDATED CONTRACT (WITH CONNECTIONS) ---
class FeatureContract(BaseModel):
    inputs: Dict[str, DataField] = {}
    outputs: Dict[str, DataField] = {}
    connections: Optional[Dict[str, ConnectionSpec]] = None

class FeaturePaths(BaseModel):
    core: str
    runtime: str
    generator_backend: str
    generator_frontend: str

# --- MASTER MANIFEST ---
class FeatureManifest(BaseModel):
    key: str
    name: str
    version: str
    description: Optional[str] = ""
    min_platform_version: Optional[str] = "0.1.0"

    classification: FeatureClassification
    infrastructure: FeatureInfrastructure = Field(default_factory=FeatureInfrastructure)
    contract: FeatureContract
    paths: FeaturePaths

    config: FeatureConfig = Field(default_factory=FeatureConfig)
    ui: FeatureUI = Field(default_factory=FeatureUI)
    limits: FeatureLimits = Field(default_factory=FeatureLimits)
    storage: Optional[FeatureStorage] = None
    api: FeatureApi = Field(default_factory=FeatureApi)
    
    # NEW: Tool definition (if this feature can be used as a tool)
    tool_definition: Optional[ToolDefinition] = None

    # Internal
    base_path: Optional[str] = None
    
    # NEW: Validation for agent-specific requirements
    @validator('contract')
    def validate_agent_contract(cls, v, values):
        """Validate that agent features have required connections"""
        if 'classification' in values:
            capability = values['classification'].capability
            
            # Agents should define tool connections
            if capability == 'agent':
                if not v.connections or 'tools' not in v.connections:
                    # Warning, not error (allow flexibility)
                    pass
            
            # Triggers should have no inputs
            if capability == 'trigger':
                if v.inputs:
                    raise ValueError('Trigger features should not have inputs')
        
        return v
    
    @validator('tool_definition')
    def validate_tool_definition(cls, v, values):
        """Validate tool definition for tool-type features"""
        if 'classification' in values:
            capability = values['classification'].capability
            
            # Tools should have a tool_definition
            if capability == 'tool' and not v:
                raise ValueError('Features with capability="tool" must include a tool_definition')
        
        return v


# --- HELPER FUNCTIONS ---
def is_agent_feature(manifest: FeatureManifest) -> bool:
    """Check if a feature is an agent"""
    return manifest.classification.capability == "agent"

def is_tool_feature(manifest: FeatureManifest) -> bool:
    """Check if a feature can be used as a tool"""
    return (
        manifest.classification.capability == "tool" or
        manifest.tool_definition is not None
    )

def is_trigger_feature(manifest: FeatureManifest) -> bool:
    """Check if a feature is a trigger"""
    return manifest.classification.capability == "trigger"

def get_tool_definition(manifest: FeatureManifest) -> Optional[ToolDefinition]:
    """Get tool definition if feature can be used as a tool"""
    return manifest.tool_definition

def get_connection_requirements(manifest: FeatureManifest) -> Dict[str, ConnectionSpec]:
    """Get connection requirements for a feature"""
    if manifest.contract.connections:
        return manifest.contract.connections
    return {}