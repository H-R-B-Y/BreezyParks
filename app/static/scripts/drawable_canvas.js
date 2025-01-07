const drawable_canvas = document.getElementById("drawingCanvas");
const drawable_context = drawable_canvas.getContext("2d", {willReadFrequently:true});
const drawable_bgcol = "#FFFFFF";
const paper_note_drawcol = (drawable_drawcol) ? "#000000" : drawable_drawcol;
let drawable_mode = "draw";
let drawable_isdrawing = false;
drawable_context.strokeStyle = paper_note_drawcol;
drawable_context.lineWidth = 1;
drawable_context.lineJoin = 'round';  // Smooth out sharp corners
drawable_context.lineCap = 'round';   // Smooth out line ends

function get_offset(e)
{
	const rect = drawable_canvas.getBoundingClientRect();
	const x = e.clientX - rect.left;
	const y = e.clientY - rect.top;
	return { x, y };
}

drawable_canvas.addEventListener("mousedown", (e) => {
		e.preventDefault();
		drawable_isdrawing = true;drawable_context.beginPath();drawable_context.moveTo(e.offsetX, e.offsetY);
});

drawable_canvas.addEventListener("touchstart", (e) => {
		e.preventDefault();
		const {x, y} = get_offset(e.touches[0]);
		drawable_isdrawing = true;drawable_context.beginPath();drawable_context.moveTo(x, y);
});

drawable_canvas.addEventListener("mousemove", (e) => {
		e.preventDefault();
		const x = e.offsetX;
		const y = e.offsetY;
		if (drawable_isdrawing) {
			if (drawable_mode === "draw"){
				drawable_context.lineTo(x, y);
				drawable_context.stroke();
			} else if (drawable_mode === "erase") {
				const imageData = drawable_context.getImageData(x - 2, y -2, 4, 4);
				const data = imageData.data;
				for (let i = 0; i < data.length; i += 4)
				{
					data[i] = 0;
					data[i + 1] = 0;
					data[i + 2] = 0;
					data[i + 3] = 0;
				}
				drawable_context.putImageData(imageData, x - 2, y - 2);
			}
		}
});

drawable_canvas.addEventListener("touchmove", (e) => {
		e.preventDefault();
		erase_size = 3;
		const {x, y} = get_offset(e.touches[0]);
		if (drawable_isdrawing) {
			if (drawable_mode === "draw"){
				drawable_context.lineTo(x, y);
				drawable_context.stroke();
			} else if (drawable_mode === "erase") {
				const imageData = drawable_context.getImageData(x - erase_size, y - erase_size, erase_size * 2, erase_size * 2);
				const data = imageData.data;
				for (let i = 0; i < data.length; i += 4)
				{
					data[i] = 0;
					data[i + 1] = 0;
					data[i + 2] = 0;
					data[i + 3] = 0;
				}
				drawable_context.putImageData(imageData, x - erase_size, y - erase_size);
			}
		}
});

drawable_canvas.addEventListener("mouseleave", (e) => {
		drawable_isdrawing = false;
});

drawable_canvas.addEventListener("touchleave", (e) => {
	drawable_isdrawing = false;
});

function set_draw_mode()
{
	if (drawable_mode == "draw"){return;}
	drawable_context.strokeStyle = paper_note_drawcol;
	drawable_context.lineWidth = 1;
	drawable_mode = "draw";
}

function set_erase_mode()
{
	if (drawable_mode == "erase"){return;}
	drawable_context.strokeStyle = drawable_bgcol;
	drawable_context.lineWidth = 1;
	drawable_mode = "erase";
}

drawable_canvas.addEventListener("mouseup", () => {drawable_isdrawing = false;});
drawable_canvas.addEventListener("touchend", () => {drawable_isdrawing = false;});

function clear_canvas() {drawable_context.clearRect(0, 0, drawable_canvas.width, drawable_canvas.height);}