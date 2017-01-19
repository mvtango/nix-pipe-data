REMOTE := mvirtel@vm-hetzner:/home/mvirtel/projekte/

.PHONY: deploy

deploy :
	rsync -v ./counter.py $(REMOTE)counter.py
