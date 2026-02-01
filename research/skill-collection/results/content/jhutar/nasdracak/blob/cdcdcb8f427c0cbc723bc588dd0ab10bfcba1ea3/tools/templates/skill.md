ID: {{ entity.id }}
Jméno: {{ entity.name }}
Popis: {{ entity.description }}
Pravidlo: {{ entity.rule }}
Poznámka: {{ entity.note }}
Kdo může použít: {{ entity.who }}
Bonus na: {{ entity.bonus }}
Vyžaduje: {{ entity.requires | join(', ') }}
