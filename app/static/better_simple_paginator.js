// <!-- Please be aware that I suck at JS and that the following code is just the quickest way I could get what I wanted out of the site. -->
async function fetch_posts(page)
{
	try {
		const response = await fetch(data_endpoint + `?page=${page}`);
		const posts = await response.json();
		return posts;
	} catch (error) {
		console.error("Error fetching new posts: ", error);
		return {};
	};
};
function render_post(post)
{
	let new_rendered = loader_template.replace(/{{id}}/g, post.id).replace(/{{title}}/g, post.title).replace(/{{created_date}}/g, post.created_date);
	console.log(new_rendered);
	return new_rendered;
};
function create_new_row(container)
{
		let this_row = document.createElement('div');
		container.appendChild(this_row);
		this_row.classList.add("w3-row-padded");
		return this_row;
};
function render_posts(posts) {
	if (!posts)
	{return ;}
		const container = document.getElementById('data-container');
		let rows = container.getElementsByClassName('w3-row-padded');
		let this_row = rows[rows.length - 1] || create_new_row(container);
		for (let i = 0; i < posts.length; i++) {
				if (this_row.children.length === 3) {
						this_row = create_new_row(container);
				}
				this_row.insertAdjacentHTML('beforeend', render_post(posts[i]));
		}
}
async function get_page()
{
	const posts = await fetch_posts(1);
	render_posts(posts.data);
}
document.getElementById("load-more").addEventListener("click", async function () 
{
	const button = this;
	const nextPage = parseInt(button.dataset.page) + 1;
	const posts = await fetch_posts(nextPage);
	if (posts && posts.data.length > 0)
	{
		render_posts(posts.data);
		button.dataset.page = nextPage;
	}
	if (!posts || posts.data.length === 0 || posts.last_page == true)
	{
		button.textContent = "No more posts";
		button.disable = true;
	}
});
get_page();