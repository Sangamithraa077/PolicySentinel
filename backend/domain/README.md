# domain/ — Domain Layer (the architectural core)

The innermost layer in Clean Architecture. Contains pure business concepts and rules with **zero dependencies** on frameworks, databases, or external services. Every other layer depends inward on `domain/` — never the reverse.

> Note: this folder was added beyond your explicit list because a Domain Layer (entities + interfaces/ports + domain exceptions) is what makes the "Presentation / Application / Domain / Infrastructure" separation you asked for actually enforceable, rather than just a naming convention over `models/`, `schemas/`, and `services/`.

## Structure
- `entities/` — core business objects (Policy, Conflict, RedundancyGroup, StalenessFlag, ...)
- `interfaces/` — abstract ports that Infrastructure implementations must satisfy
- `exceptions/` — business-rule violation exceptions
