from dataclasses import dataclass, field


@dataclass
class ChecklistField:
    id: str
    label: str
    field_type: str   # 'text' | 'textarea' | 'checkbox'
    required: bool
    order: int
    active: bool = True


@dataclass
class Video:
    id: str
    title: str
    category: str     # 'armwrestling' | 'gamedev' | 'misc'
    stage: str        # 'ideas' | 'planning' | 'filming' | 'editing' | 'posting'
    checklist_values: dict
    created_at: float
    updated_at: float

    def progress(self, fields: list) -> float:
        active = [f for f in fields if f.active]
        if not active:
            return 1.0
        filled = sum(
            1 for f in active
            if (f.field_type == "checkbox" and self.checklist_values.get(f.id))
            or (f.field_type != "checkbox" and str(self.checklist_values.get(f.id, "")).strip())
        )
        return filled / len(active)
