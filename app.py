from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import pycountry
import os

app = Flask(__name__)
app.secret_key = "atlas-secret-key"

# --------------------
# Game State
# --------------------

used_places = []
players = []
player_lives = {}
current_player_index = 0

COUNTRY_ALIASES = {
    "usa": "United States",
    "us": "United States",
    "america": "United States",
    "uk": "United Kingdom",
    "uae": "United Arab Emirates"
}


# --------------------
# Country Validation
# --------------------

def is_valid_country(country_name):

    country_name = country_name.lower()

    for country in pycountry.countries:

        if country.name.lower() == country_name:
            return True

        if hasattr(country, "official_name"):
            if country.official_name.lower() == country_name:
                return True

    return False


# --------------------
# Life System
# --------------------
def lose_life():

    global current_player_index

    if not players:
        return False

    current_player = players[current_player_index]

    player_lives[current_player] -= 1

    flash(
        f"💔 {current_player} lost a life! "
        f"({player_lives[current_player]} remaining)"
    )

    if player_lives[current_player] <= 0:

        flash(f"💀 {current_player} has been eliminated!")

        player_lives.pop(current_player)

        eliminated_index = current_player_index

        players.pop(eliminated_index)

        # Winner
        if len(players) == 1:

            flash(f"🏆 {players[0]} wins the game!")

            current_player_index = 0

            return True

        # No players left (safety)
        if len(players) == 0:

            current_player_index = 0

            return True

        # Fix index
        if current_player_index >= len(players):
            current_player_index = 0

    return False
# --------------------
# Home
# --------------------

@app.route("/", methods=["GET", "POST"])
def home():

    global current_player_index

    # --------------------
    # Start Game
    # --------------------

    if request.method == "POST" and "start_game" in request.form:

        players.clear()
        used_places.clear()
        player_lives.clear()

        for i in range(1, 7):

            player = request.form.get(f"player{i}", "").strip()

            if player:
                players.append(player)

        if len(players) < 2:

            players.clear()

            flash("❌ Please enter at least 2 players.")

            return redirect(url_for("home"))

        current_player_index = 0

        for player in players:
            player_lives[player] = 3

        flash(f"🎮 Game started with {len(players)} players!")

        return redirect(url_for("home"))

    # --------------------
    # Current Letter
    # --------------------

    current_letter = None

    if len(used_places) > 0:
        current_letter = used_places[-1][-1].upper()

    # --------------------
    # Submit Country
    # --------------------

    if request.method == "POST" and "place" in request.form:

        place = request.form["place"].strip()

        if place == "":
            flash("❌ Please enter a country.")
            return redirect(url_for("home"))

        lower_place = place.lower()

        if lower_place in COUNTRY_ALIASES:
            place = COUNTRY_ALIASES[lower_place]

        # Invalid country
        if not is_valid_country(place):

            if lose_life():
                return redirect(url_for("home"))

            return redirect(url_for("home"))

        normalized_place = place.lower()

        normalized_used_places = [
            p.lower() for p in used_places
        ]

        # Duplicate country
        if normalized_place in normalized_used_places:

            flash(f"❌ {place} has already been used!")

            if lose_life():
                return redirect(url_for("home"))

            return redirect(url_for("home"))

        # Wrong starting letter
        if current_letter and place[0].upper() != current_letter:

            flash(
                f"❌ Country must start with '{current_letter}'"
            )

            if lose_life():
                return redirect(url_for("home"))

            return redirect(url_for("home"))

        # Valid move
        used_places.append(place)

        flash(f"✅ {place} accepted!")

        current_player_index += 1

        if current_player_index >= len(players):
            current_player_index = 0

        return redirect(url_for("home"))

    # --------------------
    # Display Data
    # --------------------

    current_player = None

    if len(players) > 0:

        current_player_index = min(
            current_player_index,
            len(players) - 1
        )

        current_player = players[current_player_index]

    last_place = None

    if len(used_places) > 0:
        last_place = used_places[-1]

    return render_template(
        "index.html",
        players=players,
        current_player=current_player,
        current_letter=current_letter,
        last_place=last_place,
        player_lives=player_lives,
        total_places=len(used_places)
    )


# --------------------
# Timer Expired
# --------------------
@app.route("/next_turn")
def next_turn():

    global current_player_index

    if len(players) > 0:

        flash("⏰ Time's up!")

        eliminated = lose_life()

        # Someone won
        if eliminated:
            return redirect(url_for("home"))

        # Only move to next player if current player survived
        if len(players) > 1:

            current_player_index += 1

            if current_player_index >= len(players):
                current_player_index = 0

    return redirect(url_for("home"))
# --------------------
# Reset Game
# --------------------

@app.route("/reset")
def reset():

    global current_player_index

    confirm = request.args.get("confirm")

    if confirm != "yes":
        return render_template("confirm_reset.html")

    used_places.clear()
    players.clear()
    player_lives.clear()

    current_player_index = 0

    flash("🔄 Game ended!")

    return redirect(url_for("home"))


# --------------------
# PWA Files
# --------------------

@app.route("/manifest.json")
def serve_manifest():

    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "manifest.json"
    )


@app.route("/sw.js")
def serve_sw():

    response = send_from_directory(
        os.path.join(app.root_path, "static"),
        "sw.js"
    )

    response.headers["Service-Worker-Allowed"] = "/"

    return response


# --------------------
# Run App
# --------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )