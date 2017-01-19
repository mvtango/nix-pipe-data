REMOTE := mvirtel@vm:/home/mvirtel/projekte/

.PHONY: deploy

deploy :
	rsync -v ./counter.py $(REMOTE)counter.py
