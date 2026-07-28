# Overview

Many applications need to store data as **key-value pairs** rather than as individual fields or lists.

For example:

- Product attributes
- HTTP headers
- Application configuration
- Environment variables
- Language translations
- User preferences
- Metadata
- Labels and tags

Without a dedicated map type, developers would have to define repeated key-value messages manually, making schemas more verbose and difficult to maintain.

Protocol Buffers solve this problem by providing the **`map`** type.

A map stores a collection of key-value pairs, allowing values to be efficiently looked up using a unique key. It behaves similarly to dictionaries in Python, maps in Java, unordered maps in C++, or hash maps in many other programming languages.

This chapter explains how maps work, how they are serialized, their supported key types, and the best practices for using them in Protocol Buffer schemas.

---

# What is a Map?

A map is a collection of **key-value pairs**.

Each key uniquely identifies a corresponding value.

Example:

```text
Language

↓

English  → Hello

French   → Bonjour

German   → Hallo

Spanish  → Hola
```

Instead of searching through a list, applications can directly retrieve a value using its key.

---

# Why Do We Need Maps?

Consider storing HTTP headers.

Without maps:

```proto
message Header {

    string key = 1;

    string value = 2;

}

message Request {

    repeated Header headers = 1;

}
```

Although this works, finding a specific header requires searching through the list.

Using a map is much cleaner.

```proto
message Request {

    map<string, string> headers = 1;

}
```

Now each header is accessed directly using its key.

---

# Declaring a Map

The syntax is simple.

```proto
map<key_type, value_type> field_name = field_number;
```

Example:

```proto
message Configuration {

    map<string, string> settings = 1;

}
```

Here:

- `string` is the key type.
- `string` is the value type.
- `settings` is the field name.

---

# Map Key Types

Not every Protocol Buffer data type can be used as a key.

Supported key types include:

- int32
- int64
- uint32
- uint64
- sint32
- sint64
- fixed32
- fixed64
- sfixed32
- sfixed64
- bool
- string

Message types and floating-point types cannot be used as keys.

---

# Map Value Types

Map values are much more flexible.

They can be:

- Scalar types
- Enums
- Messages

Example:

```proto
map<string, Employee> employees = 1;
```

Each key maps to an entire `Employee` message.

---

# Basic Example

```proto
message Student {

    map<string, int32> marks = 1;

}
```

Possible data:

```text
Mathematics → 95

Physics     → 88

Chemistry   → 91
```

Applications can retrieve marks directly by subject name.

---

# Maps with Message Values

Maps often store complex objects.

Example:

```proto
message Address {

    string city = 1;

    string country = 2;

}

message OfficeDirectory {

    map<string, Address> offices = 1;

}
```

Possible data:

```text
India

↓

Address

United States

↓

Address

Germany

↓

Address
```

Each key references an entire message.

---

# Generated Code

Maps are generated as native map or dictionary types in most programming languages.

| Language | Generated Type |
|----------|----------------|
| Python | dict |
| Java | Map<K, V> |
| Go | map[K]V |
| C# | MapField<TKey, TValue> |
| C++ | Map<Key, Value> |

This allows developers to use familiar language features.

---

# Serialization

Internally, a map is represented as a collection of key-value entries.

Conceptually, the following declaration:

```proto
map<string, string> headers = 1;
```

is treated similarly to:

```proto
message HeaderEntry {

    string key = 1;

    string value = 2;

}

message Request {

    repeated HeaderEntry headers = 1;

}
```

This transformation is handled automatically by the Protocol Buffer compiler.

Developers continue working with the simpler `map` syntax.

---

# Duplicate Keys

Each key in a map must be unique.

Example:

```text
Language

↓

English → Hello

English → Hi
```

Only one value can exist for the key `"English"`.

If duplicate keys are encountered during parsing, the last value typically replaces the previous one.

---

# Empty Maps

Like repeated fields, maps default to an empty collection.

Example:

```proto
message Settings {

    map<string, string> values = 1;

}
```

Default state:

```text
values

↓

{}
```

Applications can safely iterate over the map even when it contains no entries.

---

# Real-World Example

Consider a product catalog.

```proto
message Product {

    int32 id = 1;

    string name = 2;

    map<string, string> attributes = 3;

}
```

Possible data:

```text
Color    → Black

Storage  → 256 GB

Display  → OLED

Warranty → 2 Years
```

Instead of creating separate fields for every possible attribute, the map provides a flexible solution.

---

# Maps vs Repeated Messages

Consider storing translations.

Using repeated messages:

```proto
message Translation {

    string language = 1;

    string text = 2;

}

message Greeting {

    repeated Translation translations = 1;

}
```

Using a map:

```proto
message Greeting {

    map<string, string> translations = 1;

}
```

The map version is:

- Simpler
- Easier to read
- Faster to access by key
- More concise

However, if each entry requires additional fields beyond a key and value, a repeated message may be the better choice.

---

# Common Use Cases

Maps are frequently used for:

- Configuration settings
- HTTP headers
- Environment variables
- Product attributes
- Labels
- Metadata
- Feature flags
- Language translations
- User preferences
- Dynamic properties

---

# Best Practices

When using maps:

- Use meaningful key names.
- Choose stable and unique keys.
- Use message values for complex data.
- Keep map contents logically related.
- Prefer maps for lookup-based data rather than ordered collections.
- Document the expected format of keys and values.

---

# Common Mistakes

Avoid the following mistakes:

- Using floating-point numbers as map keys.
- Expecting maps to preserve insertion order.
- Using maps when duplicate keys are required.
- Storing unrelated information in the same map.
- Replacing structured messages with maps unnecessarily.

---

# Key Takeaways

- A map stores data as key-value pairs.
- Maps simplify schemas that require lookup-based data structures.
- Supported key types include integers, booleans, and strings.
- Values can be scalar types, enums, or message types.
- Maps are represented as native dictionary or map types in generated code.
- They are ideal for configuration data, metadata, headers, translations, and other dynamic key-value relationships.