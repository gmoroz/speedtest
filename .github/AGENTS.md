# ci

- Проверки проекта добавляй в make-цели кубиков (mk/<кубик>.mk), а не в workflow: workflow выполняет только `make install` и `make full-check`.
- `.github/workflows/` не трогай: правки после генерации сотрутся при copier update.
