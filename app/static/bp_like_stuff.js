
async function bp_toggle_like_on_item(callee, type_of_thing, id_of_thing, callee_count_elem)
{
	let callee_elem = document.getElementById(callee);
	let callee_count = document.getElementById(callee_count_elem);
	let callee_origin = callee_elem.getAttribute("href");
	callee_elem.setAttribute("href", "javascript:void(0);")
	// potential to use set as it is more performant?
	if (typeof type_of_thing != "string" || !["blog_post", "comment", "thing", "profile"].includes(type_of_thing))
	{
		console.error("Type not recognised")
		return ;
	};
	let real_endpoint = "/like/" + type_of_thing + "/" + id_of_thing;
	try
	{
		const response = await fetch(real_endpoint, {method : "POST",});
		if (!response.ok)
		{
			throw new Error(`HTTP error! Status: ${resposne.status}`);
		}
		let resp_json = await response.json();
		let liked_state = resp_json.state;
		if (liked_state == "unliked")
		{
			callee_elem.innerText = "Like"; // Note: This should be changed to an icon in the future.
			callee_count.innerText = parseInt(callee_count.innerText) - 1;
		}
		else if (liked_state == "liked")
		{
			callee_elem.innerText = "Unlike"; // Note: This should be changed to an icon in the future.
		}
		if (callee_count && resp_json.count)
		{
			callee_count.innerText = resp_json.count;
		}
	}
	catch (error)
	{
		console.log("There was an error liking " + type_of_thing + " with id:" + id_of_thing);
	}
	finally
	{
		callee_elem.setAttribute("href", callee_origin);
	}
	return ;
}
