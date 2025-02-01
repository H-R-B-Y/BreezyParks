
class Player {
	constructor(username){
		this.username = username;
		this.sprite = null;
		this.usernameText = null;
		this.ready = null;
	}

	loadSprite (drawContainer){
		this.usernameText = new PIXI.Text({text:this.username, style:{fill:"#fff"}});
		this.usernameText.anchor.set(0.5,1);
		
		fetch('/'+this.username+'/sprite').then(response => {
			if (!response.ok){throw new Error("Not OK")};
			return response.json();
		}).then(async data => {
			var texture = await PIXI.Assets.load(data.sprite);
			this.sprite = PIXI.Sprite.from(data.sprite);
		}).catch(async error => {
			//console.log(error);
			var texture = await PIXI.Assets.load("/static/images/generichamster.png");
			this.sprite = PIXI.Sprite.from("/static/images/generichamster.png");
		}).then(() => {
			this.sprite.width = 64;
			this.sprite.height = 64;
			this.sprite.anchor.set(0.5,0.5);
			this.setPosition(parseInt(window.innerWidth/2), parseInt(window.innerHeight/2));
			this.sprite.zindex = 5; // why do we set it to 5?
			drawContainer.addChild(this.sprite);
			drawContainer.addChild(this.usernameText);
			this.ready = true;
		});
	}
	setPosition (x, y) {
		if (!this.ready){
			setTimeout((()=>{this.setPosition(x,y)}).bind(this), 100);
			return;
		}
		// this needs to not only set the position of the sprite 
		// but also the position of the name/anything attached to the player
		if (this.sprite){
			this.sprite.x = x;
			this.sprite.y = y;
		}
		if (this.usernameText){
			this.usernameText.x = x;
			this.usernameText.y = y - parseInt(this.sprite.height/2);
		}
	}
}
