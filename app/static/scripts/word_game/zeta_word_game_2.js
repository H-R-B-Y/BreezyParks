// This code may be shifted to a greater library after development as they might be useful

function prepend_array(array, item) {
	let new_array = array.slice();
	new_array.unshift(item);
	return new_array;
}

function getColourFromValue (colourValue) {
	return `#${colourValue.toString(16).padStart(6, '0')}`;
}

function hexToRgb(hex) {
	hex = hex.replace(/^#/, ""); // Remove '#' if present
	if (hex.length === 3) {
		hex = hex.split("").map(c => c + c).join(""); // Expand short form like #FFF to #FFFFFF
	}
	let r = parseInt(hex.substring(0, 2), 16);
	let g = parseInt(hex.substring(2, 4), 16);
	let b = parseInt(hex.substring(4, 6), 16);
	return [r, g, b];
}

function getBrightness(r, g, b) {
	return (0.299 * r) + (0.587 * g) + (0.114 * b);
}

function getContrastingColor(hexColor) {
	let [r, g, b] = hexToRgb(hexColor);
	return getBrightness(r, g, b) < 128 ? "#FFFFFF" : "#000000";
}

// endblock

// Expect player class to be loaded!!

class Grid {
	constructor(game, parentContainer, gridSize, squareSize) {
		this.game = game

		this.gridSize= gridSize;
		this.squareSize = squareSize;

		this.parentContainer = parentContainer;

		this.grid = []; // 2D array to store squares

		this.context = null;
		
		this.container = new PIXI.Container({}); // Container for the grid
		this.container.interactive = true;
		this.container.eventMode = 'dynamic';
		this.container.on("pointerleave", (() => {this.game.dropContext = null;this.dragging=false;}).bind(this))
		this.container.on("wheel", this.onScroll.bind(this));

		this.dragging = false;
		this.startpos = {x:0,y:0};
		this.container.eventMode = 'dynamic';
		this.container.on("pointerdown", this.dragStart.bind(this));
		this.container.on("pointerup", this.dragEnd.bind(this));


		this.offset = {x:0,y:0};
		this.startOffset = {x:0,y:0};
		this.scale_dir = 1;
		this.container.x = (game.app.screen.width / 2) - (squareSize * gridSize)/2;
		this.container.y = (game.app.screen.height / 2) - (squareSize * gridSize)/2;

		parentContainer.addChild(this.container);

		this.initGrid();

	}

	dragStart (event) {
		if (!this.dragging && !this.game.holdingTile)
		{
			this.dragging = true;
			this.startpos = {x:event.global.x, y:event.global.y};
			this.startOffset = {x:this.offset.x, y:this.offset.y};
			this.container.on("pointermove", this.onDrag.bind(this));
		}
	}
	onDrag (event) {
		if (this.dragging)
		{
			let diff = {x: event.global.x - this.startpos.x, y: event.global.y - this.startpos.y};
			this.offset.x = this.startOffset.x + diff.x;
			this.offset.y = this.startOffset.y + diff.y;
			this.centerGrid();
		}
	}
	dragEnd () {
		if (this.dragging && !this.game.holdingTile)
		{
			this.dragging = false;
			this.container.off("pointermove");
		}
	}

	// I literally have no way to test this OMG
	// onPinchZoom (event) {
	// 	if (event.data.originalEvent.touches && event.data.originalEvent.touches.length === 2) {
	// 		// Two-finger pinch logic
	// 		const touch1 = event.data.getLocalPosition(this.container);
	// 		const touch2 = event.data.getLocalPosition(this.container);
	// 		const pinchDistance = this.getDistance(touch1, touch2);
	
	// 		if (pinchStartDistance === 0) {
	// 			pinchStartDistance = pinchDistance;
	// 			pinchStartScale = this.container.scale.x;
	// 		} else {
	// 			const scaleFactor = pinchDistance / pinchStartDistance;
	// 			this.setZoom(scaleFactor);
	// 		}
	// 	}
	// }

	onScroll (event) {
		// I have been struggling with trying to get the zoom onto the pointer for so long i give up.
	
		let direction = (event.deltaY > 0 ? 1 : -1); // 1 for zooming in, -1 for zooming out
		let zoomFactor = 0.1;  // Adjust this value for faster/slower zooming
		
		this.setZoom(zoomFactor, direction);
	}

	setZoom (zoomFactor, direction) {
		// let p1 = {x:this.container.width / 2, y:this.container.height / 2};
		// Calculate new size based on scroll direction
		let newWidth = this.container.width + direction * zoomFactor * this.container.width;
		let newHeight = this.container.height + direction * zoomFactor * this.container.height;
		
		// Avoid scaling the container to 0 or negative sizes
		if (newWidth < 10 || newHeight < 10) return;
		// Resize the container using setSize
		this.container.setSize(newWidth, newHeight);
		// let p2 = {x:this.container.width / 2, y:this.container.height / 2};
		// this.offset.x += p1.x - p2.x;
		// this.offset.y += p1.y - p2.y;
		this.centerGrid();
	}

	createSquare (x, y) {
		const squareContainer = new PIXI.Container();
		const square = new PIXI.Graphics();
		square.rect(0, 0, this.squareSize, this.squareSize)
			.fill("#1f2122")
			.roundRect(0, 0, this.squareSize, this.squareSize, ((x == (this.gridSize/2 - 0.5)) && (y == (this.gridSize/2 - 0.5)) ? 100 : 0) )
			.stroke({ color: 0xffffff, pixelLine: true, width: 1 })

		// Set position
		squareContainer.x = x * this.squareSize;
		squareContainer.y = y * this.squareSize;
		square.parentContainer = squareContainer;

		// Store its grid position
		square.gridPosition = { x, y };
		square.containsTile = false;
		square.isSpecial = false;

		// Add event listeners
		squareContainer.interactive = true;
		squareContainer.on('pointerover', () => this.highlightSquare(square));
		squareContainer.on('pointerout', () => this.unhighlightSquare(square));

		// Add to container and row
		squareContainer.addChild(square)
		this.container.addChild(squareContainer);
		return square
	}

	moveSquare(square, x, y) {
		// Move the tile to its new position
		square.gridPosition = { x, y };
		square.parentContainer.x = x * this.squareSize;
		square.parentContainer.y = y * this.squareSize;
		if (square.containsTile) {
			square.containsTile.position = { x, y };
			square.containsTile.setPosition(square.x, square.y);
		}
	}

	initGrid() {
		for (let y = 0; y < this.gridSize; y++) {this.grid
			const row = [];
			for (let x = 0; x < this.gridSize; x++) {
				let sq = this.createSquare(x, y)
				row.push(sq);
			}
			this.grid.push(row);
		}
	}

	updateGridSize(newSize) {
		if (newSize == this.size){return;}
		// Ensure that game block action is in place!!!!
		let diff = Math.abs(newSize - this.gridSize);
		let inc = diff / 2;
		this.gridSize = newSize;

		let new_grid = [];

		for (let y = 0; y < this.gridSize; y++) {
			const row = [];
			for (let x = 0; x < this.gridSize; x++) {
				// Determine the original grid's new position in the center
				if (y >= inc && y < this.gridSize - inc && x >= inc && x < this.gridSize - inc) {
					let oldX = x - inc;
					let oldY = y - inc;
					this.moveSquare(this.grid[oldY][oldX], x, y)
					row.push(this.grid[oldY][oldX]);
				} else {
					// Create new squares around the old grid
					let sq = this.createSquare(x, y);
					row.push(sq);
				}
			}
			new_grid.push(row);
		}
		delete this.grid;
		this.grid = new_grid;
		this.centerGrid();
	}

	highlightSquare(square) {
		if (this.game.block_action){return};
		square.tint = 0xAAAAAA; // Highlight color
		if (square.containsTile && square.containsTile.is_played){return;}
		this.game.dropContext = square;
	}

	unhighlightSquare(square) {
		if (this.game.block_action){return};
		square.tint = 0xFFFFFF; // Default color
	}

	selectSquare(square) {
		if (this.game.block_action){return};
		square.fill(0xFF0000).rect(0, 0, this.squareSize, this.squareSize); // Change to red
	}

	getGridSize () {
		return {
			x: (this.squareSize * this.gridSize),
			y: (this.squareSize * this.gridSize)
		}
	}

	centerGrid() {
		this.container.x = this.offset.x + (((this.game.app.screen.width / 2)) - (this.container.width)/2);
		this.container.y = this.offset.y + (((this.game.app.screen.height / 2)) - (this.container.width)/2);
	}

	assignTileToSquare( tile, square ) {
		if (square.containsTile === false || tile.onSquare === square)
		{square.containsTile = tile;}
		else {console.error(`Trying to place tile ${tile.identity} on square that already contains tile ${square.containsTile.identity}.`);throw new Error("Tile already populated");}
	}

	removeTileFromSquare ( tile, square ) {
		if (square.containsTile === tile && !square.containsTile.is_played) {
			square.containsTile = false;
		}
		else if (square.containsTile !== tile) {console.error("Attempted to remove tile from a square that doesn't parent it.")}
		else {console.error(`Attempted to remove a tile that has already been played.`)}
	}

	getSquare ( x, y ) {
		if (x < 0 || y < 0){return null;}
		if (x >= this.grid.length || y >= this.grid.length){return null;}
		return this.grid[y][x];
	}

	setTileSpecial (data) {
		let x = data[0];
		let y = data[1];
		let t = data[2];
		let m = data[3];
		let sq = this.getSquare(x, y);
		if (sq.isSpecial) {return;}
		sq.specialText = new PIXI.Text({text:`${t}x${m}`, style:{fill:"#fff", fontSize: sq.width * 0.5, align: 'center'}});
		sq.parentContainer.addChild(sq.specialText);
		sq.specialText.x = (sq.width / 2) - (sq.specialText.width / 2);
		sq.isSpecial = true;
		sq.specialData = data;
	}
}

class Tile {
	constructor (game, parentContainer, identity, score, parentWord, uuid) {
		this.game = game;
		this.parentContainer = parentContainer;

		this.uuid = uuid;
		this.identity = identity;
		this.score = score;

		this.container = new PIXI.Container();
		this.container.interactive = true;
		this.container.eventMode = 'dynamic';

		this.graphic = null;
		this.text = null;

		this.size = 30;

		this.isPickedUp = false;

		this.is_placed = false;

		// This section for played tile information sent from server
			this.is_played = false;
			this.played_score = score;
			this.played_by = null;
			this.parentWord = parentWord
		// end 

		this.onSquare = false;
		this.position = null;

		parentContainer.addChild(this.container);
	}

	createGraphic (tileSize, color) {
		this.size = tileSize || 30;
		color = color || 0xA0A000;
		if (this.graphic) {
			this.graphic.destroy();
			this.text.destroy();
		}
		this.graphic = new PIXI.Graphics();
		this.graphic.roundRect(0, 0, tileSize, tileSize,10).fill(color).roundRect(0, 0, tileSize, tileSize,10).stroke({ color: 0xffffff, pixelLine: true, width: 1 });
		this.text = new PIXI.Text({text:this.identity || "#err", style:{fill:"#fff", fontSize: tileSize * 0.6, align: 'center'}});
		this.text.anchor.set(0.5,0.5);
		this.text.x = this.graphic.width / 2;
		this.text.y = this.graphic.height / 2;
		this.subtext = new PIXI.Text({text:`${this.played_score}`, style:{fill:"#fff", fontSize: tileSize * 0.3, align: 'center'}});
		
		this.subtext.x += this.subtext.width / 2;
		this.subtext.y += 2;
		this.container.addChild(this.graphic);
		this.container.addChild(this.text);
		this.container.addChild(this.subtext);
		

	}

	setHandEvents (val) {
		if (val === true)
		{
			this.onGlobalMouseMove = this.onDragTile.bind(this);
			this.onGlobalMouseUp = this.onReleased.bind(this);
			// On mouse down "pickup" the tile.
			this.container.on("pointerdown", this.onClicked.bind(this));
			this.container.on("pointerenter", this.addToContext.bind(this));
			this.container.on("pointerleave", this.removeFromContext.bind(this));
		}
		else {
			this.onGlobalMouseMove = ()=>{};
			this.onGlobalMouseUp = ()=>{};
			// On mouse down "pickup" the tile.
			this.container.off("pointerdown");
			this.container.off("pointerenter");
			this.container.off("pointerleave");
		}
	}

	setPosition (x,y) {
		this.container.x = x;// - (this.size / 2);
		this.container.y = y;// - (this.size / 2); 
	}

	del () {
		this.text.destroy();
		this.graphic.destroy();
		this.container.destroy();
	}

	changeParent (newParent) {
		this.parentContainer.removeChild(this.container);
		this.parentContainer = newParent;
		this.parentContainer.addChild(this.container);
	}

	onClicked (event) { // Click event is unique as it should only trigger in the context of the tile, while drag and release are in the context of the window.
		if (this.game.block_action){return};
		this.isPickedUp = true;
		this.game.holdingTile = true;
		if (this.is_placed) {			
			if (event.data.originalEvent.pointerType === 'mouse' && event.data.originalEvent.button == 2)
			{
				this.returnToHandOnRightClick();
				return;
			}
			this.game.dropContext = this.onSquare;
		}
		this.changeParent(this.game.uiContainer);
		this.setPosition(event.pageX - (this.size / 2), event.pageY - (this.size / 2));
		this.container.interactive = false;
		this.container.interactiveChildren = false;
		window.addEventListener("pointermove", this.onGlobalMouseMove);
		window.addEventListener("pointerup", this.onGlobalMouseUp);
		this.game.ui.orderTilesInHand();
	}
 
	onDragTile (event) {
		if (this.game.block_action){return};
		// Update position
		const rect = this.game.app.canvas.getBoundingClientRect();
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;

		this.setPosition(mouseX - this.size / 2, mouseY - this.size / 2);
	}

	updateGlobalDropContext (what) {
		if (this.game.block_action){return};
		what = what || this;
		if (!this.isPickedUp) {
			this.game.dropContext = what;
		}
	}

	addToContext () {
		if (!this.is_placed && !this.is_played)
		{this.updateGlobalDropContext(this);}
		else if (this.game.holdingTile) {
			this.updateGlobalDropContext(null);
		}
	}

	removeFromContext () {
		this.updateGlobalDropContext(null);
	}

	onReleased (event) {
		if (this.game.block_action){return};
		this.isPickedUp = false;
		this.game.holdingTile = false;
		// Stop tracking the tile globally
		window.removeEventListener("pointermove", this.onGlobalMouseMove);
		window.removeEventListener("pointerup", this.onGlobalMouseUp);

		this.container.interactive = true;
		this.container.interactiveChildren = true;
		this.game.handleTilePlacement(this);
	}

	_placeOnSquare ( square ) {
		this.is_placed = true;
		this.changeParent(square.parentContainer);
		this.setPosition(square.x, square.y);
		this.position = square.gridPosition;
		this.onSquare = square;
	}

	placeOnSquare ( square ) {
		if (this.game.block_action){return};
		if (this.is_played) {throw new Error("Cannot place a tile that is already played.")}
		this.is_placed = true;
		this.changeParent(square.parentContainer);
		this.setPosition(square.x, square.y);
		this.position = square.gridPosition;
		this.onSquare = square;
	}

	returnToHandOnRightClick () {
		if (this.game.block_action){return};
		if (this.onSquare)
		{
			this.game.holdingTile = false;
			this.isPickedUp = false;
			this.is_placed = false;
			this.game.removeTileFromGrid( this, this.onSquare);
			this.game.resetWordCheckerTimer();
		} else {
			this.returnToHand();
		}
	}

	returnToHand (  ) {
		if (this.game.block_action){return};
		if (this.is_played) {throw new Error("Cannot return a tile to hand that is not part of your hand.")}
		this.is_placed = false;
		this.changeParent(this.game.ui.handContainer);
		this.game.ui.orderTilesInHand();
		this.position = null;
		this.onSquare = false;
	}

}

class Word {
	/*
	A word is a collection of tiles THAT HAS BEEN PLAYED,
	they will be sent from the server in some form
	*/
	constructor (game, tiles, word, uuid, axis, owner) {
		this.game = game;
		this.board = game.board;
		this.owner = owner;
		this.tiledata = tiles;
		this.tiles = {}
		this.uuid = uuid;
		this.word = word;
		this.meaning = null;
		this.superseeded_by = null;
		this.axis = axis;
	}

	drawWord () {
		let t = null;
		for (let i = 0; i < this.tiledata.length; i++) {
			t = this.tiledata[i];
			console.log(t);
			let newt = new Tile(this.game, this.game.board.container, t.identity, t.played_score, this, t.id);
			newt.is_played = true;
			newt.played_by = t.played_by;
			newt.createGraphic(50, 0x252525);
			let sq = this.game.board.getSquare(t.pos.x, t.pos.y);
			if (sq.containsTile.is_placed) {
				this.game.returnTileToHand(sq.containsTile);
			}
			newt._placeOnSquare(sq);
			this.game.board.assignTileToSquare(newt, sq);
			this.tiles[newt.uuid] = newt;
		}
		//console.log(this);
	}
}
//#region UI
class UI {
	constructor (game, parentContainer) {
		this.tSize = 50;
		this.tMargin = 20;
		this.handData = [];
		this.hand = [];
		this.score = 0;
		
		this.game = game;
		this.parentContainer = parentContainer;
		
		this.handContainer = new PIXI.Container();
		this.handGraphic = new PIXI.Graphics();
		this.draw_handContainer();
		this.handContainer.y = game.app.screen.height - this.handGraphic.height;
		this.handContainer.x = (game.app.screen.width - this.handGraphic.width)/ 2;
		this.handContainer.addChild(this.handGraphic);
		
		this.submitButtonEnabled = false;
		this.drawSubmitButton();
		
		this.maxDiscards = 0;
		this.discardsRemaining = 0;
		this.discardButtonEnabled = true;
		this.discardContainer = new PIXI.Container();
		this.discardContainer.interactive = true;
		this.discardTarget = new PIXI.Graphics();
		this.discardText = new PIXI.Text();
		this.drawDiscardTarget();

		this.parentContainer.addChild(this.discardContainer);
		this.parentContainer.addChild(this.handContainer);
		this.game.resizeEvents.push(this.onResizeEvent.bind(this));

		this.smaller_ui = false;
	}

	setDiscardContext (event) {
		if (this.game.holdingTile) {
			this.game.dropContext = "discard";
		}
	}

	unsetDiscardContext (event) {
		this.game.dropContext = null;
	}

	disableDiscardButton () {
		this.discardCountText.text = this.getDicardCountText();
		if (this.discardButtonEnabled === false){return;}
		this.discardButtonEnabled = false;
		console.log("disabling discard button.");
		this.discardTarget.clear().roundRect(0,0,this.discardText.width,this.discardText.width, 10).fill(0x151515);
		this.discardContainer.off("pointerenter");
	}

	enableDiscardButton () {
		this.discardCountText.text = this.getDicardCountText();
		if (this.discardButtonEnabled === true){return;}
		this.discardButtonEnabled = true;
		console.log("enabling discard button.");
		this.discardTarget.clear().roundRect(0,0,this.discardText.width,this.discardText.width, 10).fill(0x5f0000);
		this.discardContainer.on("pointerenter", this.setDiscardContext.bind(this));
	}

	getDicardCountText( ) {
		return `${this.discardsRemaining} / ${this.maxDiscards}`;
	}

	drawDiscardTarget () {
		this.discardText.text = "Discard";
		this.discardText.x += 35;
		this.discardText.y += 5;
		this.discardText.style.fontSize = 35;
		this.discardText.rotation = Math.PI / 4;
		
		this.discardTarget
		.roundRect(0,0,this.discardText.width,this.discardText.width, 10)
		.fill(0x5f0000);

		this.discardCountText = new PIXI.Text({
			text: this.getDicardCountText(),
			style: {
				fontSize: 20,
			}
		});
		
		this.discardContainer.x = this.game.app.screen.width - (5 + this.discardTarget.width);
		this.discardContainer.y = this.game.app.screen.height - (5 + this.discardTarget.height);
		
		this.discardContainer.addChild(this.discardTarget);
		this.discardContainer.addChild(this.discardText);
		this.discardContainer.addChild(this.discardCountText);

		this.discardCountText.y -= this.discardCountText.height;
		this.discardCountText.x += (this.discardTarget.width / 2) - (this.discardCountText.width / 2);

		this.discardContainer.on("pointerenter", this.setDiscardContext.bind(this));
		this.discardContainer.on("pointerleave", this.unsetDiscardContext.bind(this));
	}

	drawSubmitButton () {
		this.submitButton = new PIXI.Container();
		this.submitButtondDestroyed = false;
		this.submitButtonEnabled = false;
		this.submitButtonGraphic = new PIXI.Graphics();
		this.submitButtonText = new PIXI.Text(
			{text:"submit", style:{fill:"#fff", fontSize: 25, align: 'center'}}
		);
		this.submitButton.interactive = true
		this.submitButton.buttonMode = true;
		this.submitButton.cursor = 'not-allowed';
		this.submitButton.addChild(this.submitButtonGraphic);
		this.submitButton.addChild(this.submitButtonText);
		this.submitButtonGraphic
			.roundRect(0, 0, (this.tMargin * 2) + this.submitButtonText.width, (this.tMargin * 2) + this.submitButton.height,5)
			.fill(0x252525);
		//this.submitButtonText.anchor.set(0.5,0.5)
		this.submitButtonText.x = this.tMargin;
		this.submitButtonText.y = this.tMargin;
		this.submitButton.y = this.handContainer.y - this.submitButtonGraphic.height;
		this.submitButton.x = this.handContainer.x + (this.handGraphic.width / 2) - (this.submitButtonGraphic.width / 2);
		this.parentContainer.addChild(this.submitButton);
	}

	draw_handContainer () {
		this.handGraphic
			.roundRect(0, 0, this.tMargin + ((this.tSize + this.tMargin) * 7), this.tMargin * 2 + this.tSize,10)
			.fill(0xAFAF00)
	}

	swapTilesInHand (tile, tile2) {
		let pos1 = this.hand.indexOf(tile);
		let pos2 = this.hand.indexOf(tile2);
		this.hand[pos1] = tile2;
		this.hand[pos2] = tile;
		tile.returnToHand();
	}

	updateHand (handData) {
		// update the hand graphics here.
		this.handData = handData;
		//console.log(this.handData);
		let t = [];
		if (this.hand.length != 0){
			let newids = this.handData.map(t => t.id);
			for (let mytile in this.hand) {
				if (!newids.includes(this.hand[mytile].uuid))
				{
					this.removeTileFromHand(this.hand[mytile]);
				}
			}
			for (let dataTile in this.handData) {
				let inhand = false;
				for (let handTile in this.hand) {
					if (this.hand[handTile].uuid == this.handData[dataTile].id) {
						inhand = true;
					}
				}
				if (!inhand) {
					t = new Tile(this.game, this.handContainer, this.handData[dataTile].identity, this.handData[dataTile].score, null, this.handData[dataTile].id);
					t.setHandEvents(true);
					this.hand.push(t);
				}
			}
		}
		else {
			for (let i = 0; i < this.handData.length; i++){
				let c = this.handData[i].identity;
				t = new Tile(this.game, this.handContainer, c, this.handData[i].score, null, this.handData[i].id);
				t.setHandEvents(true);
				this.hand.push(t);
			}
		}
		this.orderTilesInHand();
	}

	// For exact match
	removeTileFromHand (tile) {
		this.hand = this.hand.filter((t) => t !== tile);
		tile.del();
	}

	// There should be no duplicates! so this should be ok
	// Logged to console if above assertion is false
	removeTilebyId(tileId) {
		let tile = this.hand.filter((t) => t.uuid === tileId);
		if (tile.length > 1) {console.error(`Something has gone severly wrong, multiple tiles with ${tileId} exist!`);};
		this.removeTileFromHand(tile[0]);
	}


	orderTilesInHand () {
		let tileToOrder = [];
		this.hand.forEach((t) => {
			if (!t.is_placed && !t.isPickedUp){tileToOrder.push(t)};
		});

		// space to fill 
		let spaceToFill = this.handGraphic.width - (2 * this.tMargin);
		let spaceNeeded = (((this.tMargin + this.tSize) * tileToOrder.length) - this.tMargin);
		let startOffset = (spaceToFill - spaceNeeded) / 2;

		for (let i = 0; i < tileToOrder.length; i++) {
			let t = tileToOrder[i];
			if (!t.graphic){t.createGraphic(this.tSize)};
			t.setPosition(
				this.tMargin + startOffset + (i * (this.tMargin + this.tSize)),
				this.tMargin
			);
		}
	}

	onResizeEvent () {
		this.handContainer.y = game.app.screen.height - this.handContainer.height;
		this.handContainer.x = (game.app.screen.width - this.handContainer.width)/ 2;
		if(this.submitButtondDestroyed == false)
		{
			this.submitButton.y = this.handContainer.y - this.submitButtonGraphic.height;
			this.submitButton.x = this.handContainer.x + (this.handGraphic.width / 2) - (this.submitButtonGraphic.width / 2);
		}
		if (!this.smaller_ui)
		{
		this.discardContainer.x = this.game.app.screen.width - (5 + this.discardContainer.width);
		this.discardContainer.y = this.game.app.screen.height - (5 + this.discardContainer.height);
		}
		else { 
			this.discardContainer.x = this.game.app.screen.width - (5 + this.discardContainer.width);
			this.discardContainer.y = this.game.app.screen.height - (this.handContainer.height * 0.8) - this.discardContainer.height;
		}
	}

	enableSubmitButton () {
		if (this.submitButtondDestroyed){return;}
		if (this.submitButtonEnabled){return;}
		this.submitButtonEnabled = true;
		this.submitButtonText.text = "Submit" + (this.tempScore ? ` ( ${this.tempScore} )` : "");
		this.submitButtonGraphic.clear().roundRect(0, 0, (this.tMargin * 2) + this.submitButtonText.width, (this.tMargin * 2) + this.submitButton.height,5).fill(0x005a00);
		this.submitButton.cursor = 'pointer';
		this.submitButton.on("pointerup", this.submitButtonPressed.bind(this));
	}

	submitButtonPressed () {
		if (!this.submitButtonEnabled){return;}
		//console.log("submitting words!")
		this.game.submitWord();
	}

	disableSubmitButton () {
		this.tempScore = 0;
		if (this.submitButtondDestroyed){return;}
		if (!this.submitButtonEnabled){return;}
		this.submitButtonEnabled = false;
		this.submitButtonText.text = "Submit";
		this.submitButtonGraphic.clear().roundRect(0, 0, (this.tMargin * 2) + this.submitButtonText.width, (this.tMargin * 2) + this.submitButton.height,5).fill(0x252525);
		this.submitButton.cursor = 'not-allowed';
		this.submitButton.off("pointerup");
	}

	destroySubmitButton () {
		this.submitButtondDestroyed = true;
		this.parentContainer.removeChild(this.submitButton);
		this.submitButtonGraphic.destroy();
		this.submitButtonText.destroy();
		this.submitButton.destroy();
	}
}
//#endregion

class WordProto {
	constructor (){
		this.is_parent_word = null;
		this.word = '';
		this.new_tile_positions = {};
		this.new_tiles = [];
		this.all_tiles = [];
		this.axis = null;
		this.all_tile_position = [];
		this.score = 0;
		this.word_mult = 1;
	}

	append_tile (tile) {
		//  Check if tile is in hand?
		if (tile.is_placed && !tile.is_played && !tile.played_by) {
			this.new_tiles.push(tile.uuid);
			this.new_tile_positions[tile.uuid] = tile.position;
		}
		this.word = this.word + tile.identity;
		this.all_tiles.push(tile.uuid);
		this.all_tile_position.push(tile.position);
		// if tile is placed just add played score
		// else check for mults
		if (tile.is_played) {
			this.score += tile.played_score;
		} else {
			if (tile.onSquare.isSpecial) {
				if (tile.onSquare.specialData[2] === "t") {
					this.score += tile.score * tile.onSquare.specialData[3];
				} else {
					this.word_mult *= tile.onSquare.specialData[3];
					this.score += tile.score;
				}
			} else {
				this.score += tile.score;
			}
		}
	}

	prepend_tile (tile) {
		// check if tile is in hand?
		if (tile.is_placed && !tile.is_played && !tile.played_by) {
			this.new_tiles = prepend_array(this.new_tiles, tile.uuid);
			this.new_tile_positions[tile.uuid] = tile.position;
		}
		this.word = tile.identity + this.word;
		this.all_tiles = prepend_array(this.all_tiles, tile.uuid);
		this.all_tile_position = prepend_array(this.all_tile_position, tile.position);
		if (tile.is_played) {
			this.score += tile.played_score;
		} else {
			if (tile.onSquare.isSpecial) {
				if (tile.onSquare.specialData[2] === "t") {
					this.score += tile.score * tile.onSquare.specialData[3];
				} else {
					this.word_mult *= tile.onSquare.specialData[3];
					this.score += tile.score;
				}
			} else {
				this.score += tile.score;
			}
		}
	}
	
	getScore () {
		return this.score * this.word_mult;
	}
}

class PlayerHalo {

	constructor (game, parentContainer, radius, center) {
		this.game = game;
		this.parentContainer = parentContainer; 

		this.players = [];
		this.usernames = [];
		this.lookup = {};

		this.radius = radius;
		this.center = center;
		this.container = new PIXI.Container();

		this.parentContainer.addChildAt(this.container, 0);

		this.timeoutRefresh = null;
	}

	addPlayer (username) { 
		if (this.usernames.includes(username)){return;};
		this.usernames.push(username);
		let p = new Player(username);
		this.players.push(p);
		this.lookup[username] = p;
		p.loadSprite(this.container);
	}

	organisedRefresh () {
		clearTimeout(this.timeoutRefresh);
		this.timeoutRefresh = setTimeout(this.orderPlayerHalo.bind(this), 500);
	}

	orderPlayerHalo () {
		let inc = (Math.PI * 2) / this.players.length;

		let theta = 0;


		for (let i = 0; i < this.players.length; i++) {
			let x = this.center.x + this.radius * Math.cos(theta);
			let y = this.center.y + this.radius * Math.sin(theta);

			this.players[i].setPosition(x, y);

			theta += inc;
		}
	}

	reCenter () {
		this.center = {x: window.innerWidth / 2, y: window.innerHeight / 2};
		this.orderPlayerHalo();
	}
}

class ScoreRow {
	constructor (username, score, bgCol, fgCol, width) {
		this.container  = new PIXI.Container();
		this.nameText = new PIXI.Text(
			{text:username + ": ", style:{fill:fgCol, fontSize: 20, align: 'center'}}
		); 
		this.scoreText  = new PIXI.Text(
			{text:score, style:{fill:fgCol, fontSize: 20, align: 'center'}}
		);
		this.bg = new PIXI.Graphics();
		console.log(bgCol);
		this.bg.rect(0,0,width, 5 + this.nameText.height + 5).fill(bgCol);
		this.container.addChild(this.bg);
		this.container.addChild(this.nameText);
		this.nameText.x += 5;
		this.nameText.y += 5;
		this.container.addChild(this.scoreText);
		this.scoreText.x = 210 - this.scoreText.width;
		this.scoreText.y += 5;
	}
	del () {
		this.nameText.destroy();
		this.scoreText.destroy();
		this.bg.destroy();
		this.container.destroy();
	}
}

class ScoreBoard {
	constructor (game, parentContainer, players) {
		this.game = game;
		this.players = players;
		this.parentContainer = parentContainer;

		this.scoreBoardOpen = false;
	}

	initialiseDisplay () {
		this.container = new PIXI.Container();
		this.container.interactive = true;
		this.parentContainer.addChild(this.container);

		// at first just display a small tab, add a click event to expand the tab;
		this.displayBump = new PIXI.Graphics();
		this.displayBump.interactive = true;
		this.displayBump.roundRect(0,0,50,window.screen.height/4,5).fill(0x8f8f8f);
		this.displayBump.x -= 10;
		this.container.addChild(this.displayBump);
		this.displayBumpText = new PIXI.Text(
			{text:"Scores", style:{fill:"#fff", fontSize: 20, align: 'center'}}
		)
		this.displayBumpText.rotation = Math.PI * 1.5;
		this.displayBumpText.x = 5;
		this.displayBump.y = window.screen.height / 3;
		this.displayBumpText.y = this.displayBump.y + (this.displayBumpText.width / 2) + (this.displayBump.height / 2);
		this.container.addChild(this.displayBumpText);
		this.displayBump.on("pointerup", this.displayScoreBoard.bind(this));
		this.displayBumpText.interactive = true;
		this.displayBumpText.on("pointerup", this.displayScoreBoard.bind(this));
	}

	
	displayScoreBoard () {
		if (this.scoreBoardOpen){return;}
		this.scoreBoardOpen = true;
		let count = this.players.length;
		let height = 10;
		let sorted = this.players.slice().sort((a,b) =>  b.score - a.score );
		this.scores = sorted.map(s => new ScoreRow(s.username, s.score || 0, s.colour, s.text_colour, 210));
		for (let i = 0; i < sorted.length; i++){
			let s = this.scores[i];
			this.container.addChild(s.container)
			s.container.y = this.displayBump.y + 30 + ((s.nameText.height + 10)* (i));
		}
		this.closeButton = new PIXI.Graphics();
		this.closeButton.interactive = true;
		this.closeButton.rect(0,0,210,30).fill(0x150000);
		this.closeButton.y = (window.screen.height / 3);
		this.container.addChild(this.closeButton);
		this.closeText = new PIXI.Text(
			{text:"Close", style:{fill:"#fff", fontSize: 20, align: 'center'}}
		);
		this.container.addChild(this.closeText);
		this.closeText.x = this.closeButton.width/2 - this.closeText.width /2;
		this.closeText.y = (window.screen.height / 3);
		this.closeButton.on("pointerup", this.closeScoreBoard.bind(this));
		this.closeText.interactive = true;
		this.closeText.on("pointerup", this.closeScoreBoard.bind(this));
		
	}

	closeScoreBoard () {
		if (!this.scoreBoardOpen){return;}
		this.scoreBoardOpen = false;
		this.closeButton.destroy();
		this.closeText.destroy();
		for (let i = 0; i < this.scores.length; i++) {
			let s = this.scores[i];
			s.del();
		}
	}

	onResizeEvent () 
	{
		this.displayBump.y = window.screen.height / 3;
		this.displayBumpText.y = this.displayBump.y + (this.displayBumpText.width / 2) + (this.displayBump.height / 2);
	}
	
}

class GameState {
	constructor (namespace, username, canvas) {
		this.canvas = canvas;
		this.app = new PIXI.Application();
		this.app.init({
			eventMode : 'dynamic',
			canvas : canvas,
			background :  0x1F2122,
			resizeTo : window,
		});

		this.username = username
		
		this.resizeEvents = [];
		this.gameContainer = new PIXI.Container();
		this.gameContainer.interactive = true;
		this.gameContainer.eventMode = 'dynamic';
		this.app.stage.addChild(this.gameContainer);
		
		this.uiContainer = new PIXI.Container();
		this.uiContainer.interactive = true;
		this.uiContainer.eventMode = 'dynamic';
		this.app.stage.addChild(this.uiContainer);
		
		this.playerHalo = null;
		
		this.words = {};
		this.ui = null;
		this.board = null;
		
		new ResizeObserver(this.onResize.bind(this)).observe(document.documentElement);
		window.addEventListener("resize", this.onResize.bind(this));
		
		this.socket = io("/zeta/"+namespace);
		this.socket_initial_recv = 0;
		
		this.socket.on("connect", this.onSocketConnected.bind(this));
		this.socket.on("disconnect", this.onSocketDisconnected.bind(this));
		
		this.holdingTile = false;
		this.dropContext = null;
		
		this.block_action = false;
		this.wordCheckTimeout = null;
		this.submittable_word_data = null;
		this.expectingResponse = false;
	}

	handleSpecialTiles (data) {
		for (let i = 0; i < data.length; i++) {
			this.board.setTileSpecial(data[i]);
		}
	}

	onUpdateGameState (data) {
		console.log(data);
		if (!this.board && !data.board_size){
			throw new Error("No board size returned from server");
		}

		if (this.board === null){
			this.board = new Grid(this, this.gameContainer, data.board_size, 50);
			this.resizeEvents.push(this.board.centerGrid.bind(this.board));
		}
		
		if (this.ui === null){
			this.ui = new UI(this, this.uiContainer);
			if (data.max_discards)
			{
				this.ui.maxDiscards = data.max_discards;
			}
			if (this.app.screen.width < 600)
			{
				this.ui.smaller_ui = true;
				this.ui.handContainer.setSize(
					this.ui.handContainer.width * 0.8,
					this.ui.handContainer.height * 0.8
				);
				this.ui.discardContainer.setSize(
					this.ui.discardContainer.width * 0.8,
					this.ui.discardContainer.height * 0.8
				);
				this.ui.onResizeEvent();
			}
		}

		if (data.special_tiles) {
			this.handleSpecialTiles(data.special_tiles);
		}

		if (data.words_played) {
			this.drawWords(data.words_played);
		}
		
		this.callUpdatePlayerState();

		if (this.playerHalo === null) 
		{
			this.playerHalo = new PlayerHalo(
				this, this.gameContainer, 
				Math.min(Math.sqrt(Math.pow(this.board.getGridSize().x/2, 2) + Math.pow(this.board.getGridSize().y/2, 2)) + 60 * 0.8, this.app.screen.width * 0.8),
				{x: window.innerWidth / 2, y: window.innerHeight / 2}
			);
			this.playerHalo.addPlayer(this.username);
			this.playerHalo.lookup[this.username].colour = getColourFromValue(data.colour);
			this.playerHalo.lookup[this.username].score = data.score;
			this.playerHalo.lookup[this.username].text_colour = getContrastingColor(this.playerHalo.lookup[this.username].colour);
			this.score = data.score;
			this.playerHalo.organisedRefresh();
			this.resizeEvents.push(this.playerHalo.reCenter.bind(this.playerHalo));
			this.scoreboard = new ScoreBoard(this, this.uiContainer, this.playerHalo.players);
			this.resizeEvents.push(this.scoreboard.onResizeEvent.bind(this.scoreboard))
			this.scoreboard.initialiseDisplay();
			this.socket.on("joined", this.onPlayerJoined.bind(this));
			this.socket.emit("request_players", {});
		}

	}

	onUpdatePlayerState (data) {
		// This is a different approach to the other functions, 
		// I really am just testing the water with JS, not sure on the best approach.
		if (!data.username || data.username != this.username){throw new Error("Wrong player data returned from server.")}
		if (Object.hasOwn(data, "tiles")){
			if (this.ui.handData != data.tiles){this.ui.updateHand(data.tiles)};
		}else{throw new Error("No hand provided")}
		if (Object.hasOwn(data, "allowed_turn")){
			if (data.allowed_turn === false) {
				if (this.ui === null) {
					console.log("Couldn't destory submit button, do something here!")
				}
				else {
					this.ui.destroySubmitButton();
				}
			} else {
				if (this.ui.submitButtondDestroyed)
				{
					this.ui.drawSubmitButton();
				}
			}
		} else {console.log("Player state did not contain information about turn state.")}
		if (Object.hasOwn(data, "allowed_discard") && Object.hasOwn(data, "discards_remaining"))
		{
			if (this.ui === null) {
				console.log("Couldn't destory submit button, do something here!")
			}
			else {
				this.ui.discardsRemaining = data.discards_remaining;
				if (data.allowed_discard) {
					this.ui.enableDiscardButton();
				} else {
					this.ui.disableDiscardButton();
				}
			}
		}
	}

	async callUpdatePlayerState () {
		try {
			const response = await fetch("get_state");
			if (!response.ok){throw new Error("State was not ok.")}
			const data = await response.json();
			if (data.status === "success") { 
				this.onUpdatePlayerState(data.state);
			} else {
				throw new Error("State status was not ok", data);
			}
		} catch (error) {
			console.error(error);
		}
	}

	onNewWord (data) {
		//console.log(data);
		// this.ui.disableDiscardButton();
		this.drawWords([data.word,]);
		this.checkWords();
		if (this.scoreboard.scoreBoardOpen)
		{
			this.scoreboard.closeScoreBoard();
			this.scoreboard.displayScoreBoard();
		}
	}

	onPlayerJoined (data) {
		console.log("joined", data);
		if (data.username == this.username){return ;}
		this.playerHalo.addPlayer(data.username);
		this.playerHalo.lookup[data.username].score = data.score;
		this.playerHalo.lookup[data.username].colour = getColourFromValue(data.colour);
		this.playerHalo.lookup[data.username].text_colour = getContrastingColor(this.playerHalo.lookup[data.username].colour);
		this.playerHalo.organisedRefresh();
		if (this.scoreboard.scoreBoardOpen)
		{
			this.scoreboard.closeScoreBoard();
			this.scoreboard.displayScoreBoard();
		}
	}

	onUpdateScore (data) {
		console.log("Score updated: ",data);
		if (!data.username || !this.playerHalo.usernames.includes(data.username)){
			return;
		}
		this.playerHalo.lookup[data.username].score = data.score;
		console.log(`${data.username} and ${this.username}`);
		if (data.username == self.username) {
			this.score = data.score;
		}
		if (this.scoreboard.scoreBoardOpen)
		{
			this.scoreboard.closeScoreBoard();
			this.scoreboard.displayScoreBoard();
		}
	}

	async onBoardResized (data) {
		this.block_action = true;
		this.board.updateGridSize(data.size || this.board.size);
		this.playerHalo.radius = Math.sqrt(Math.pow(this.board.getGridSize().x/2, 2) + Math.pow(this.board.getGridSize().y/2, 2)) + 60;
		if(data.special_tiles){this.handleSpecialTiles(data.special_tiles)};
		this.block_action = false;
	}

	onResetting (data) {
		this.resetting = true;
		console.log("Server is resetting!");
	}

	onSocketConnected () {
		if (this.socket_initial_recv) {return;}
		this.socket_initial_recv = 1;
		this.socket.on("board_state", this.onUpdateGameState.bind(this));
		this.socket.on("player_state", this.onUpdatePlayerState.bind(this));
		this.socket.on("new_word", this.onNewWord.bind(this));
		this.socket.on("score_updated", this.onUpdateScore.bind(this));
		this.socket.emit("request_game_state", {"timestamp" : null});
		this.socket.on("board_resized", this.onBoardResized.bind(this));
		this.socket.on("game_reset", this.onResetting.bind(this));
		window.addEventListener("keydown", this.onKeyboardEvent.bind(this));
	}

	// Not a great solution but it works for now!
	async reloadTimout () {
		this.reloadCount++;
		const resp = await fetch("state_check");
		if (!resp.ok){console.error("failed to check game state")}
		else{
			const j = await resp.json();
			if (j.status === "success")
			{
				if (j.resetting && this.reloadCount < 5)
				{
					setTimeout(this.reloadTimout.bind(this), 2000);
					return;
				}
				else if (j.resetting && this.reloadCount >= 5) {
					await fetch(`/flashme/${encodeURIComponent("server encountered an error connecting to game")}/error`);
					window.location.href = "/";
				} else {
					window.location.reload();
				}
			}
		}
	}

	onSocketDisconnected () {
		console.log("lost connection to socket.")
		if (this.resetting){
			this.reloadCount = 0
			console.log("closing socket");
			this.socket.close()
			setTimeout( this.reloadTimout.bind(this), 500);
		}
		// should handle safely here or server gets spammed with requests.
	}

	onResize () {
		for (let i = 0; i < this.resizeEvents.length; i++) {this.resizeEvents[i]()};
	}

	// handle it here as the containers cannot get key events it seems?
	onKeyboardEvent (event) {
		console.log(event);
		if (["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","r"].includes(event.key)) {
			if (event.key === "ArrowLeft") {
				this.board.offset.x -= this.board.container.width * 0.05;
			} else if (event.key === "ArrowRight") {
				this.board.offset.x += this.board.container.width * 0.05;
			} else if (event.key === "ArrowUp") {
				this.board.offset.y -= this.board.container.height * 0.05;
			} else if (event.key === "ArrowDown") {
				this.board.offset.y += this.board.container.height * 0.05;
			} else if (event.key === "r"){
				this.board.offset = {x:0, y:0};
				this.board.container.setSize(750);
			}
			this.board.centerGrid();
		}
	}

	drawWords (words) {
		let word = null;
		for (let i = 0; i < words.length; i++) {
			word = words[i];
			if (this.words[word.id]){continue;}
			//console.log(word);
			let neww = new Word(this, word.tiles, word.word, word.id, word.axis, word.owner);
			this.words[word.id] = neww;
			neww.drawWord();
		}
		this.colourWordsTimeout()
	}

	colourWords () {
		if (!this.playerHalo){this.colourWordsTimeout(); return;}
		let word = null;
		let parent = null;
		for (let i in this.words) {
			word = this.words[i];
			parent = word.owner;
			if (!this.playerHalo.lookup[word.owner].colour){continue;}
			for (let key in word.tiles)
			{
				word.tiles[key].graphic.clear();
				word.tiles[key].createGraphic(50, this.playerHalo.lookup[word.owner].colour);
				word.tiles[key].text.style.fill = this.playerHalo.lookup[word.owner].text_colour;
				word.tiles[key].subtext.style.fill = this.playerHalo.lookup[word.owner].text_colour;
			}
			word.isColoured = true;
		}
	}

	colourWordsTimeout () {
		clearTimeout(this.colourTimer);
		this.colourTimer = setTimeout(
			this.colourWords.bind(this),
			100
		)
	}

	placeTileOnGrid ( tile, square ) {
		if (square.containsTile && square.containsTile !== tile) {throw new Error("Square already contains a letter.")}
		if (tile.is_played) {throw new Error("Cannot place a tile that is played")};
		if (tile.is_placed) {this.board.removeTileFromSquare(tile, tile.onSquare)};
		this.board.assignTileToSquare( tile, square );
		tile.placeOnSquare( square );
	}

	removeTileFromGrid ( tile, square ) {
		if (!square.containsTile) {throw new Error("Cannot remove tile from empty square.")}
		this.board.removeTileFromSquare( tile, square );
		tile.returnToHand();
	}

	resetWordCheckerTimer() {
		clearTimeout(this.wordCheckTimeout);
		this.wordCheckTimeout = setTimeout(this.checkWords.bind(this), 500);
	}

	returnTileToHand (tile) {
		if (tile.onSquare) {
			this.removeTileFromGrid(tile, tile.onSquare);
		} else {
			tile.returnToHand();
		}
	}

	returnAllTilesToHand () {
		for (let i = 0; i < this.ui.hand.length; i++)
		{
			let tile = this.ui.hand[i];
			if (tile.is_placed) {
				this.returnTileToHand(tile);
			}
		}
	}

	handleTilePlacement ( tile ) {
		if (this.block_action){return};
		var context = this.dropContext;
		if (context && this.board.grid.some(innerArray => innerArray.some(obj => obj === context))){
			this.placeTileOnGrid( tile, this.dropContext );
		} else if ( context && this.ui.hand.includes(context) && context.is_placed != true) {
			if (tile.is_placed){this.removeTileFromGrid( tile, tile.onSquare )};
			this.ui.swapTilesInHand(tile, context);
		} else if (context && context === "discard") {
			this.discardTile(tile);
		} else {
			this.returnTileToHand(tile);
		}
		this.resetWordCheckerTimer();
	}

	async wordIsLegal( word ){
		try {
			// load word list on server side
			let addr = word_dictionary_endpoint.replace("{{word}}", word);
			// console.log("checking word: ", addr)
			const response = await fetch(addr);
			if (response.status == 404) {return false;}
			else {
				let jsn = await response.json();
				//word.meaning = jsn;
				//console.log(jsn);
				return true;
			}
		} catch (error) {
			console.error("encountered error", error)
			return false;
		}
		return false;
	}

	async processWords ( words ) {
		console.log(words);
		const result = await Promise.all(words.map(word => this.wordIsLegal(word.word)));
		const allSame = result.every(result => result === true);
		if (allSame) {
			// console.log("Words are ok!");
			const sum = (arr) => arr.reduce((a, b) => a + b, 0);
			this.ui.tempScore = sum(
				words.map((w) => w.getScore())
			);
			this.ui.enableSubmitButton();
		}
		else {
			console.log("One or more word is not ok!");
			this.ui.disableSubmitButton();
		}
	}

	async discardTile (tile) {
		this.block_action = true;
		try {
			const resp = await fetch(`discard/${encodeURIComponent(tile.uuid)}`);
			if (resp.ok) {
				const j = await resp.json();
				if (j.status === "success") {
					this.ui.removeTilebyId(tile.uuid);
				} else {
					this.block_action = false;
					this.returnTileToHand(tile);
					console.error(j.message);
				}
			}

		} finally {
			this.socket.emit("request_hand", {"timestamp" : null});
			this.block_action = false;
		}
	}

	async submitWord (  ) {
		this.block_action = true;
		// this is now defunct i believe
		this.expectingResponse = true;
		try {
			const resp = await fetch("played_word", {
				method : "POST",
				headers: {
					"Content-Type": "application/json"  // Specify JSON data format
				},
				body : JSON.stringify(this.submittable_word_data)
			});
			const data = await resp.json();

			if (data.status === "success") {
				if (data.word.tiles) {
					data.word.tiles.forEach((t) => {
						this.ui.removeTilebyId(t.id);
					});
				} else {
					console.error("Word accepted, no tile data sent from server.");
				}
				this.socket.emit("request_hand", {"timestamp" : null});
				
			} else {
				console.error("Submitted word was not accepted: ", data);
				// return played tiles to hand
				this.returnAllTilesToHand();

			}
		} catch (error) {
			console.log(error);
		} finally {
			this.block_action = false;
			this. expectingResponse = false;
		}
	}

	checkWords (  ) {
		this.ui.disableSubmitButton();
		let tilesToCheck = [];
		for (let i = 0; i < this.ui.hand.length; i++){if (this.ui.hand[i].is_placed){tilesToCheck.push(this.ui.hand[i])}};
		// console.log(tilesToCheck);

		let primary_word = new WordProto();
		primary_word.is_parent_word = true;


		let rows = new Set();
		let cols = new Set();
		tilesToCheck.forEach(t => {
			rows.add(t.position.y);
			cols.add(t.position.x);
		});
		if (rows.size !== 1  && cols.size !== 1) {return ;}


		let is_horiz = rows.size === 1;

		// If both rows and cols are 1 then we need to check for aligned tiles
		// Because an extension takes precident over a single letter

		if (rows.size === 1 && cols.size === 1)
		{
			if ([...rows][0] < this.board.gridSize - 1 && this.board.getSquare([...cols][0], [...rows][0] + 1).containsTile)
			{
				is_horiz = false;
			}
			else if ([...rows][0] > 0 && this.board.getSquare([...cols][0], [...rows][0] - 1).containsTile)
			{
				is_horiz = false;
			}
		}
		
		//primary_word_data.axis = is_horiz ? "h" : "v";
		//this counts the tiles played in order to get the word information.
		if ( is_horiz ) {
			primary_word.axis = 'h';
			let row = [...rows][0]; // This is so foul lol
			// ... is spread (converts iterable to array)
			// then index 0 ;
			let cols_to_check = tilesToCheck.map(t => t.position.x)
			//console.log(cols_to_check)
			let min_col = Math.min(...cols_to_check);
			let max_col = Math.max(...cols_to_check);
			//console.log(`iterating: ${min_col} and ${max_col} at row ${row}`)
			for (let col = min_col; col < max_col + 1; col++) {
				let tile = this.board.grid[row][col].containsTile;
				//console.log(`Tile ${tile}`);
				if (tile){
					primary_word.append_tile(tile);
				}
				else {return};
			}
			// Check if tile is superseeding.
			if (min_col > 0){
				if (this.board.grid[row][min_col - 1].containsTile){
					for (let col = min_col - 1; col >= 0; col--) {
						let t = this.board.grid[row][col].containsTile;
						if (t) {
							primary_word.prepend_tile(t);
						} else {
							break;
						}
					}
				}
			}
			if (max_col < this.board.grid.length - 1) {
				if (this.board.grid[row][max_col + 1].containsTile) {
					for (let col = max_col + 1; col < this.board.grid.length; col++) {
						let t = this.board.grid[row][col].containsTile;
						if (t) {
							primary_word.append_tile(t);
						} else {
							break;
						}
					}
				}
			}
			let max_min = (Math.max(...primary_word.all_tile_position.map(s => s.x))
				- Math.min(...primary_word.all_tile_position.map(s => s.x))) + 1;
			if (max_min != primary_word.all_tiles.length){return;}
		} else {
			primary_word.axis = 'v';
			let col = [...cols][0]; 
			let rows_to_check = tilesToCheck.map(t => t.position.y);
			let min_row = Math.min(...rows_to_check);
			let max_row = Math.max(...rows_to_check);
			for (let row = min_row; row < max_row + 1; row++) {
				let tile = this.board.grid[row][col].containsTile;
				if (tile){
					primary_word.append_tile(tile);
				}
				else {return};
			}
			// Check if tile is superseeding.
			if (min_row > 0){
				if (this.board.grid[min_row - 1][col].containsTile){
					for (let row = min_row - 1; row >= 0; row--) {
						let t = this.board.grid[row][col].containsTile;
						if (t) {
							primary_word.prepend_tile(t);
						} else {
							break;
						}
					}
				}
			}
			if (max_row < this.board.grid.length - 1) {
				if (this.board.grid[max_row + 1][col].containsTile) {
					for (let row = max_row + 1; row < this.board.grid.length; row++) {
						let t = this.board.grid[row][col].containsTile;
						if (t) {
							primary_word.append_tile(t);
						} else {
							break;
						}
					}
				}
			}
			let max_min = (Math.max(...primary_word.all_tile_position.map(s => s.y))
				- Math.min(...primary_word.all_tile_position.map(s => s.y))) + 1;
			if (max_min != primary_word.all_tiles.length){return;}
		}

		let words = []
		//console.log(primary_word);
		words.push(primary_word);
		// Check for adjacent words:
		this.getAdjacentWords(tilesToCheck, is_horiz,).forEach(
			w => 
			words.push(w)
		);
		
		let validate = false;
		if (Object.values(this.words).length == 0)
		{
			for (let pos in primary_word.all_tile_position)
			{
				if (primary_word.all_tile_position[pos].x == (this.board.gridSize / 2) - 0.5 && primary_word.all_tile_position[pos].x == primary_word.all_tile_position[pos].y)
				{
					validate = true;
					break;
				}
			}
			
		}
		else {
			if ((words.length > 1) || (primary_word.new_tiles.length != primary_word.all_tiles.length))
			{
				validate = true;
			}
		}
		if (!validate){return};
		this.submittable_word_data = words;
		console.log(this.submittable_word_data);
		this.processWords(words);
	}

	getAdjacentWords( placedTiles, is_horiz,) {
		let words = [];
		let tile = null;
		for (let i = 0; i < placedTiles.length; i++) {
			let adjword = new WordProto();
			tile = placedTiles[i];
			if (is_horiz) { 
				adjword.axis = 'v';
				let col = tile.position.x;
				let start_row = tile.position.y;
				if (start_row > 0) {
					for (let row = start_row -1; row >= 0; row--) {
						if (this.board.grid[row][col].containsTile){
							adjword.prepend_tile(this.board.grid[row][col].containsTile);
							// update primary word data
						} else {break;}
					}
				}
				for (let row = start_row; row < this.board.grid.length; row++) 
				{
					if (this.board.grid[row][col].containsTile){
						adjword.append_tile(this.board.grid[row][col].containsTile);
					} else {break;}
				}
			} else {
				adjword.axis = 'h';
				let row = tile.position.y;
				let start_col = tile.position.x;
				if (start_col > 0) {
					for (let col = start_col -1; col >= 0; col--) {
						if (this.board.grid[row][col].containsTile){
							adjword.prepend_tile(this.board.grid[row][col].containsTile);
							// update primary word data
						} else {break;}
					}
				}
				for (let col = start_col; col < this.board.grid.length; col++) 
				{
					if (this.board.grid[row][col].containsTile){
						adjword.append_tile(this.board.grid[row][col].containsTile);
					} else {break;}
				}
			}
			if (adjword.word !== "" && adjword.word.length > 1){words.push(adjword);};
		}
		return words;
	}
		// //#region DEBUG
		debugResetTurnTime(username) {
			game.socket.emit("reset_turn", {"username":username || game.username});
		}
		debugForceResize (inc) {
			game.socket.emit("debug_force_increment", {"inc": inc || 1});
		}
		// //#endregion
	
}

var game = null;
const initialPath = new URL(window.location.href).pathname;
const currentPath = initialPath.split('/')[1] || '';
document.addEventListener("DOMContentLoaded", async () => {
	const zetaCanvas = document.getElementById("zetaCanvas");
	game = new GameState(currentPath, zetaCanvas.dataset.userid, zetaCanvas);
	document.addEventListener('contextmenu', (e) => e.preventDefault());
	setTimeout( () => {document.getElementById("zetaCanvas").style.display = "block";}, 100);
})