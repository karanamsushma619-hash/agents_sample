import json
import inspect

def dump_tool_schema(tool):
    print("\n" + "="*80)
    print("TOOL:", getattr(tool, "name", tool))
    print("TYPE:", type(tool))
    print("DESC:", getattr(tool, "description", None))

    args_schema = getattr(tool, "args_schema", None) or getattr(tool, "args_schema_", None)
    print("args_schema:", args_schema)
    if args_schema is None:
        print("No args_schema found on tool.")
        return

    print("args_schema type:", type(args_schema))
    # args_schema might be a class or an instance
    schema_obj = args_schema

    # If instance, get its class
    if not isinstance(args_schema, type):
        schema_obj = args_schema.__class__

    print("schema_obj:", schema_obj)
    print("schema_obj bases:", getattr(schema_obj, "__mro__", None))

    # Pydantic v2
    if hasattr(schema_obj, "model_json_schema"):
        s = schema_obj.model_json_schema()
        print("Pydantic v2 model_json_schema(): top keys =", list(s.keys()))
        print(json.dumps(s, indent=2)[:5000])
        return

    # Pydantic v1
    if hasattr(schema_obj, "schema"):
        s = schema_obj.schema()
        print("Pydantic v1 schema(): top keys =", list(s.keys()))
        print(json.dumps(s, indent=2)[:5000])
        return

    # Fallback: try json_schema (some libs)
    if hasattr(schema_obj, "json_schema"):
        s = schema_obj.json_schema()
        print("json_schema(): top keys =", list(s.keys()))
        print(json.dumps(s, indent=2)[:5000])
        return

    print("No known schema method found (schema/model_json_schema/json_schema).")

# Dump one tool
dump_tool_schema(tools[0])

# Dump all tools
for t in tools:
    dump_tool_schema(t)
