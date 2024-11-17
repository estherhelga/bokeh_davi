from bokeh.plotting import curdoc
from bokeh.models import Div
from bokeh.layouts import column

# Image URLs
aatrox_url = "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/champion/Aatrox.png"
dorans_shield_url = "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/item/1054.png"
conqueror_url = "https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/Precision/Conqueror/Conqueror.png"
flash_url = "https://ddragon.leagueoflegends.com/cdn/14.20.1/img/spell/SummonerFlash.png"

# Create Divs for each image
aatrox_div = Div(text=f"<img src='{aatrox_url}' alt='Aatrox' style='width:100px;'>", width=120, height=120)
dorans_shield_div = Div(text=f"<img src='{dorans_shield_url}' alt='Doran's Shield' style='width:100px;'>", width=120, height=120)
conqueror_div = Div(text=f"<img src='{conqueror_url}' alt='Conqueror' style='width:100px;'>", width=120, height=120)
flash_div = Div(text=f"<img src='{flash_url}' alt='Flash' style='width:100px;'>", width=120, height=120)

# Arrange the Divs in a column
layout = column(aatrox_div, dorans_shield_div, conqueror_div, flash_div)

# Add the layout to the current document
curdoc().add_root(layout)
