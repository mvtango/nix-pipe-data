REMOTE := mvirtel@vm-hetzner:/home/mvirtel/projekte/

.PHONY: deploy

deploy :
	rsync -v ./*.py $(REMOTE)
