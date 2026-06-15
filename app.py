from flask import Flask, render_template, request, redirect, url_for, flash
import pycountry

app = Flask(__name__)
app.secret_key = "atlas-secret-key"

# Game State
used_places = []
players = []
current_player_index = 0

# Common aliases players will use
COUNTRY_ALIASES = {
    "usa": "United States",
    "us": "United States",
    "america": "United States",
    "uk": "United Kingdom",
    "uae": "United Arab Emirates"
}


def is_valid_country(country_name):

    country_name = country_name.lower()

    for country in pycountry.countries:

        # Standard country name
        if country.name.lower() == country_name:
            return True

        # Official name if it exists
        if hasattr(country, "official_name"):
            if country.official_name.lower() == country_name:
                return True

    return False


@app.route("/", methods=["GET", "POST"])
def home():

    global current_player_index

    # --------------------
    # Game Setup
    # --------------------
    if request.method == "POST" and "start_game" in request.form:

        players.clear()
        used_places.clear()

        for i in range(1, 7):

            player = request.form.get(f"player{i}", "").strip()

            if player:
                players.append(player)

        if len(players) < 2:

            players.clear()

            flash("❌ Please enter at least 2 players.")

            return redirect(url_for("home"))

        current_player_index = 0

        flash(f"🎮 Game started with {len(players)} players!")

        return redirect(url_for("home"))

    # --------------------
    # Atlas Logic
    # --------------------
    current_letter = None

    if len(used_places) > 0:
        current_letter = used_places[-1][-1].upper()

    if request.method == "POST" and "place" in request.form:

        place = request.form["place"].strip()

        if place == "":
            flash("❌ Please enter a country.")

        else:

            # Convert aliases
            lower_place = place.lower()

            if lower_place in COUNTRY_ALIASES:
                place = COUNTRY_ALIASES[lower_place]

            # Validate country
            if not is_valid_country(place):

                flash(f"❌ {place} is not a valid country.")

            else:

                # Duplicate detection
                normalized_place = place.lower()

                normalized_used_places = [
                    p.lower() for p in used_places
                ]

                if normalized_place in normalized_used_places:

                    flash(f"❌ {place} has already been used!")

                elif current_letter and place[0].upper() != current_letter:

                    flash(
                        f"❌ Country must start with '{current_letter}'"
                    )

                else:

                    used_places.append(place)

                    flash(f"✅ {place} accepted!")

                    # Next player's turn
                    if len(players) > 0:

                        current_player_index += 1

                        if current_player_index >= len(players):
                            current_player_index = 0

        return redirect(url_for("home"))

    # --------------------
    # Display Data
    # --------------------
    current_player = None

    if len(players) > 0:
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
        total_places=len(used_places)
    )


@app.route("/reset")
def reset():

    global current_player_index

    confirm = request.args.get("confirm")

    if confirm != "yes":
        return render_template("confirm_reset.html")

    used_places.clear()
    players.clear()

    current_player_index = 0

    flash("🔄 Game ended!")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)