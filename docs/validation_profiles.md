# 🔍 Declarative Validation Profiles

Declarative validation profiles provide a lightweight, rule-driven mechanism for enforcing logical constraints on metadata structures—separate from traditional JSON Schema validation.

---

## ✅ Why Use Validation Profiles?

| Advantage       | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| 🎯 Precision    | Supports complex relationships not expressible in static schemas            |
| 📦 Decoupling   | Rules are external to business logic and easily editable without redeploying|
| 🔍 Transparency | Profiles live as plain-text YAML; analysts can audit and revise them easily |
| 🔄 Flexibility  | Supports context-aware rules, domain-specific thresholds, and enforcement toggling |

---

## 🛠️ Rule Structure

Validation profiles are written in YAML, consisting of a `rules:` list. Each rule must define:

- `if`: a relational expression using dot-notated key paths
- `raise`: the message shown if the condition is met

```yaml
rules:
  - if: "domain_definition.max_z <= domain_definition.min_z"
    raise: "Invalid bounds: max_z must exceed min_z"

  - if: domain_definition.nx == 0
    raise: "Grid resolution nx must be nonzero"

  - if: domain_definition.max_x < domain_definition.min_x
    raise: "max_x cannot be less than min_x"



