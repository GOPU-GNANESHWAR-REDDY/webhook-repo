async function fetchEvents() {
    try {
        const res = await fetch("/data");
        const events = await res.json();
        const container = document.getElementById("events");
        container.innerHTML = "";

        events.reverse().forEach(e => {
            let msg = "";
            if (e.action === "push") {
                msg = `${e.author} pushed to ${e.to_branch} on ${e.timestamp}`;
            } else if (e.action === "pull_request") {
                msg = `${e.author} submitted a pull request from ${e.from_branch} to ${e.to_branch} on ${e.timestamp}`;
            } else if (e.action === "merge") {
                msg = `${e.author} merged branch ${e.from_branch} to ${e.to_branch} on ${e.timestamp}`;
            }
            const div = document.createElement("div");
            div.textContent = msg;
            container.appendChild(div);
        });
    } catch (err) {
        console.error("Error fetching data:", err);
    }
}
fetchEvents();
setInterval(fetchEvents, 15000);
