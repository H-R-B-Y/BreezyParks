function my_print_bin(byte)
{
	let output = "";
	while (byte)
	{
		output += "" + (byte & 1);
		byte >>= 1;
	}
	while (output.length < 8)
	{
		output = ("" + "0") + output;
	}
	console.log("Byte: ", output.split("").reverse().join(""));
};
function paper_note_pack_black(data, width, height) {
		const packed_bytes = [];
		let byte = 0;
		let bit_count = 0;
		for (let y = 0; y < height; y++) {
			for (let x = 0; x < width; x++) {
						const index = ((y * width) + x) * 4;
						const r = data[index];
						const g = data[index + 1];
						const b = data[index + 2];
						const a = data[index + 3];
						let is_black = 0;
						if (r <= 1 && g <= 1 && b <= 1 && a != 0) {
							is_black = 1;
						}
						console.log(`r${r} r${g} r${b} r${a}`);
						byte = (byte << 1) | is_black;
						bit_count++;
						if (bit_count === 8) {
								packed_bytes.push(byte);
								byte = 0;
								bit_count = 0;
						}
				}
		}
		if (bit_count > 0) { // Push the remaining bits (pad with 0s)
				packed_bytes.push(byte << (8 - bit_count));
		}
		return new Uint8Array(packed_bytes);
};
async function paper_note_async_send ()
{
	const image_data = drawable_context.getImageData(0,0, drawable_canvas.width, drawable_canvas.height);
	const output = await paper_note_pack_black(image_data.data, drawable_canvas.width, drawable_canvas.height);
	try {
			const response = await fetch("/post_note", {
					method: "POST",
					headers: { "Content-Type": "application/octet-stream",},
					body: output,
			});

			if (!response.ok) {
					throw new Error(`HTTP error! Status: ${response.status}`);
			}

			window.location.href = "/";
	} catch (error) {
			console.error("Error:", error);
	}
};
function post_paper_note()
{
	if (drawable_canvas.width != drawable_width || drawable_canvas.height != drawable_height){return;}
	paper_note_async_send();
}