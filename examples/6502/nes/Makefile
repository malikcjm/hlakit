all: game

game: game.s
	../../../hla --platform=NES --include=../../../include/cpu --include=../../../include/platform $<

clean:
	rm -rf bin/*
