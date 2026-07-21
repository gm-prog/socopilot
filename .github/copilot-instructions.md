# GitHub Copilot Context: Socopilot Project Execution Standards

This document establishes the strict runtime, dependency, and infrastructure execution environment rules for the `socopilot` repository. Use these constraints for all terminal command generations, script updates, and debugging tasks.

---

## 1. Virtual Environment & Celery Execution Rules
* **Local Host / WSL Execution:** Always isolate dependencies. Never use global python or system-wide binaries for local testing.
* **Celery Pathing:** All local Celery worker invocations must use the explicit virtual environment binary path: `backend/.venv/bin/celery`.
* **Queue Routing Configuration:** The core asynchronous processing pipeline uses an explicit queue named `processing`. Workers must listen to this queue.
* **Concurrency Capping:** To prevent local LLM (Ollama/Mistral) resource exhaustion and timeouts, limit processing worker concurrency to a maximum of 2.

### Standard Local Worker Start Command:
```bash
DATABASE_URL="postgresql://socopilot:Test1234@127.0.0.1:5432/socopilot" backend/.venv/bin/celery -A app.workers.celery_app:celery_app worker --loglevel=info -Q1µéìŠ‰ÁÉ½•ÍÍ¥¹œ€´µ½¹ÕÉÉ•¹äôÈ)€(´´´((ŒŒ€È¸%¹™É…ÍÑÉÕÑÕÉ”•Á•¹‘•¹¥•Ì€¡½­•È½µÁ½Í”¤)Q¡”±½…°…ÁÁ±¥…Ñ¥½¸…É¡¥Ñ•ÑÕÉ”É•±¥•Ì½¸„µÕ±Ñ¤µ½¹Ñ…¥¹•È½­•ÈÍ•ÑÕÀµ…¹…•¥¸Ñ¡”‘½­•È½€‘¥É•Ñ½Éä¸€((ŒŒŒÑ¥Ù”½¹Ñ…¥¹•ÉÌ€˜A½ÉĞ5…ÑÉ¥àè(¨€¨©A½ÍÑÉ•ME0€¡İ¥Ñ ÁÙ•Ñ½È¤è¨¨A½ÉĞ€ÔĞÌÉ€(¨€¨©I•‘¥Ì€¡	É½­•È½I•ÍÕ±Ğ	…­•¹¤è¨¨A½ÉĞ€ØÌÜå€(¨€€¨©=±±…µ„€¡1½…°154¹¥¹”¤è¨¨A½ÉĞ€ÄÄĞÌÑ€(¨€¨©=Á•¹M•…É €¡M•…É ½%¹‘•á¥¹œ¹¥¹”¤è¨¨A½ÉĞ€äÈÀÁ€€¡M•ÕÉ¥Ñä¥Í…‰±•™½È1½…°•Ø¤((ŒŒŒ=Á•¹M•…É M•ÉÙ¥”MÁ•¥™¥…Ñ¥½¸è)]¡•¸ÕÁ‘…Ñ¥¹œ‘½­•Èµ½µÁ½Í”¹åµ±€°•¹ÍÕÉ”Ñ¡”½Á•¹Í•…É¡€½¹Ñ…¥¹•È‘•™¥¹¥Ñ¥½¸µ…Ñ¡•ÌÑ¡¥Ì‰±½¬ÁÉ•¥Í•±äÑ¼…Ù½¥Á±…¥¸µÑ•áĞ½¹¹•Ñ¥½¸¡…¹‘Í¡…­”™…¥±ÕÉ•Ìè)å…µ°(€½Á•¹Í•…É è(€€€¥µ…”è½Á•¹Í•…É¡ÁÉ½©•Ğ½½Á•¹Í•…É èÈ¸ÄÄ¸À(€€€½¹Ñ…¥¹•É}¹…µ”è½Á•¹Í•…É (€€€•¹Ù¥É½¹µ•¹Ğè(€€€€€€´±ÕÍÑ•È¹¹…µ”õÍ½½Á¥±½Ğµ±ÕÍÑ•È(€€€€€€´¹½‘”¹¹…µ”õ½Á•¹Í•…É (€€€€€€´‘¥Í½Ù•Éä¹ÑåÁ”õÍ¥¹±”µ¹½‘”(€€€€€€´‰½½ÑÍÑÉ…À¹µ•µ½Éå}±½¬õÑÉÕ”(€€€€€€´€‰=A9MI!})Y}=AQLôµaµÌÔÄÉ´€µaµàÔÄÉ´ˆ(€€€€€€´%M	1}MUI%Qe}A1U%8õÑÉÕ”(€€€Õ±¥µ¥ÑÌè(€€€€€µ•µ±½¬è(€€€€€€€Í½™Ğè€´Ä(€€€€€€€¡…Éè€´Ä(€€€€€¹½™¥±”è(€€€€€€€Í½™Ğè€ØÔÔÌØ(€€€€€€€¡…Éè€ØÔÔÌØ(€€€Á½ÉÑÌè(€€€€€€´€äÈÀÀèäÈÀÀ)€(´´´((ŒŒ€Ì¸…Ñ„%¹•ÍÑ¥½¸Q•ÍĞY•É¥™¥…Ñ¥½¸]½É­™±½Ü)]¡•¸İÉ¥Ñ¥¹œÑ•ÍĞÍÉ¥ÁÑÌ½ÈÙ…±¥‘…Ñ¥¹œÑ…Í¬•á•ÕÑ¥½¸Á¥Á•±¥¹•Ìè(Ä¸¹ÍÕÉ”Ñ¡”‘…Ñ…‰…Í”ÑÉ…¹Í…Ñ¥½¸½µµ¥ÑÌÑ¼A½ÍÑÉ•ME0€©‰•™½É”¨…±±¥¹œ…ÁÁ±å}…Íå¹Œ ¥€Ñ¼…Ù½¥‘½İ¹ÍÑÉ•…´±½½­ÕÀÉ…”½¹‘¥Ñ¥½¹Ì¸(È¸½Éµ…ĞÁ…å±½…‘Ì…Ì™Õ±±ä¹•ÍÑ••¹Ù•±½Á•Ì½¹™½Éµ¥¹œ‘¥É•Ñ±äÑ¼Ñ¡”…¹½¹¥…±±•ÉÑM¡•µ…€Ñ¼ÁÉ•Ù•¹ĞAå‘…¹Ñ¥ŒY…±¥‘…Ñ¥½¹ÉÉ½É€ÍÑÉÕÑÕÉ…°É•©•Ñ¥½¹Ì¸