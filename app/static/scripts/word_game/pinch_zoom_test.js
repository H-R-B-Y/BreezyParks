

var app = null;


class square_resizable {
	constructor (app, parent_container) {
		this.container = new PIXI.Container();
		this.parent_container = parent_container;


		this.graphic = new PIXI.Graphics();

		this.graphic.rect(0,0, 300, 300).fill(0xff0000);

		this.container.addChild(this.graphic);
		
		this.parent_container.addChild(this.container);

		// this.graphic.x = window.screen.width / 2 - this.graphic.width / 2;
		// this.graphic.y = window.screen.height / 2 - this.graphic.height / 2;

		this.container.interactive = true;

		this.container.on("touchstart", this.onTouch.bind(this));
		this.container.on("touchend", this.onTouchEnd.bind(this));
		this.container.on("touchmove", this.onTouchDrag.bind(this));

		this.touches = {};
		this.initial_distance = null;
		this.centerGrid();
	}
	
	onTouch (event) { 
		this.touches[event.pointerId] = { x: event.global.x, y: event.global.y };
		console.log(event.pointerId);
		let keys = Object.keys(this.touches);
		if (keys.length === 2) {
			this.initial_distance = 
			Math.floor(Math.sqrt(
				Math.pow(this.touches[keys[0]].x - this.touches[keys[1]].x, 2) +
				Math.pow(this.touches[keys[0]].y - this.touches[keys[1]].y, 2)
			)/12);
		}
	}


	onTouchDrag (event) {
		let keys = Object.keys(this.touches);
		if (keys.length === 2) {
			this.touches[event.pointerId] = { x: event.global.x, y: event.global.y }
			this.current_distance = 
			Math.floor(Math.sqrt(
				Math.pow(this.touches[keys[0]].x - this.touches[keys[1]].x, 2) +
				Math.pow(this.touches[keys[0]].y - this.touches[keys[1]].y, 2)
			)/12);
			console.log(`Initial dist: ${this.initial_distance}, curr dist: ${this.current_distance}`);
			if (this.initial_distance > this.current_distance) {
				this.setZoom(0.1, -1);
				this.initial_distance = this.current_distance;
			} else if (this.initial_distance < this.current_distance) {
				this.setZoom(0.1, 1);
				this.initial_distance = this.current_distance;
			}
			else {
				return;
			}
		}
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

	onTouchEnd (event) {
		console.log(event.pointerId);
		delete this.touches[event.pointerId];
	}

	centerGrid() {
		this.container.x = window.screen.width /2 - this.container.width /2;
		this.container.y = window.screen.height /2 - this.container.height /2;
	}

}

var square = null;

document.addEventListener("DOMContentLoaded", async () => {
	const zetaCanvas = document.getElementById("zetaCanvas");
	app = new PIXI.Application();
	app.init({
		eventMode : 'static',
		canvas : zetaCanvas,
		background :  0x1F2122,
		resizeTo : window,
	});
	setTimeout( () => {document.getElementById("zetaCanvas").style.display = "block";}, 100);
	
	square = new square_resizable(app, app.stage);
})
