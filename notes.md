v0.01
You can specify the type of house you want it to build (eg “3 bedroom apartment”).
I improved the instructions prompt to the LLM and it seems to work better.
The code now gives the LLM the edges in addition to the nodes, so it now knows what is already connected. This removed the error of suggesting already existing links.
I instructed the LLM to suggest: ADD, CONNECT, and STOP. And provide a reason for stopping.
It now finds a new label in the existing corpus and uses that. I also increased the number of imported graphs from 15 to 30 which helped a lot as new node names were added (e.g. Dining Room was never in the first 15 for some reason).
I have added a ‘patience’ parameter where if the action is not applied, it gives up after ‘n’ number of tries as long as ‘n’ is less than ‘patience’
I made the printout nicer and more readable (see image).
You can now see each graph being built node by node.