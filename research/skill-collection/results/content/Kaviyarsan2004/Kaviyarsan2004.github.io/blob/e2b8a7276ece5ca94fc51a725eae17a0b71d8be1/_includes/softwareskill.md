| Skill | Level |
| ---- | ---- |
{% assign skills = site.data.skills.software | sort: "title" -%}
{% for skill in skills -%}
| {{skill.title}} | {{skill.level}} |
{%endfor%}