


from to_do_list.model import PlanningState, PlanItem, PlanStatus


class TodoManager:
    def __init__(self):
        self.state = PlanningState()
        
    def update(self, items: list[PlanItem]) -> str:
        if len(items) > 12 :
            raise ValueError("Keep the session plan short (max 12 items)")
        
        normalized = list()
        in_progress_count = 0
        for index, raw_item in enumerate(items):
            content = raw_item.content.strip()
            status = raw_item.status.lower()
            active_form = raw_item.active_form.strip()
            
            if status == PlanStatus.in_progress:
                in_progress_count += 1
            
            normalized.append(PlanItem(
                content = content
                , status = status
                , active_form = active_form
            ))
            
        if in_progress_count > 1:
            raise ValueError("Only one plan item can be in_progress")
        
        self.state.items = normalized
        self.state.rounds_since_update = 0
        return self.render()
    
    def render(self) -> str :
        if not self.state.items:
            return "No session plan yet."
        
        marker_map = {
                PlanStatus.pending : "[ ]"
                , PlanStatus.in_progress : "[>]"
                , PlanStatus.completed : "[x]"
            }
        
        lines = list()
        
        for item in self.state.items:
            line = f"{marker_map[item.status]} {item.content}"
            if item.status == PlanStatus.pending and item.active_form:
                line += f"（{item.active_form}）"
            lines.append(line)
        
        completed = sum(1 for item in self.state.items if item.status == PlanStatus.completed)
        lines.append(f"\n({completed}/{len(self.state.items)} completed)")
        return "\n".join(lines)