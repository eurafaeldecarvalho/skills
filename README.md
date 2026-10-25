# skills

Coleção de skills do Claude. Cada skill fica na sua própria pasta, com um `SKILL.md`.

## Skills

| Skill | O que faz |
|-------|-----------|
| [`game-feel/`](game-feel/) | Game feel / "juice": a camada de feedback (easing, number-pop, screenshake, hit-stop, partículas, som, arte flat-minimalista) que faz um jogo parecer satisfatório e compartilhável. Um "impeccable, mas para jogos". |

## Instalar uma skill (Claude Code)

Copie a pasta da skill para o seu diretório de skills:

```bash
# skill no nível do usuário
cp -r game-feel ~/.claude/skills/game-feel
```

Ou coloque a pasta dentro do `.claude/skills/` de um projeto. O Claude passa a consultá-la automaticamente quando o contexto bate com a `description` da skill.

## Licença
MIT — ver [LICENSE](LICENSE).
