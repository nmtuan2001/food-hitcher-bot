# food-hitcher-bot

Inspired by our daily struggles of being too lazy to go out to buy food, having no friends to order with us and being too broke to afford the delivery fees of ordering delivery by ourselves, we created a bot for people who live in close proximity to "food hitch": find others to order food delivery with and share the delivery cost using a quick and easy Telegram bot.

You can find out more about our bot [here](https://devpost.com/software/foodhitch).

## Installation and Setting Up

*The following guide is for Windows. You might need to change the commands for UNIX.*

- If you have yet to install virtualenv, execute `python -m pip install virtualenv`.

- Setup virtual env, activate & install necessary packages:

  - `python -m venv env`
  - `.\env\Scripts\activate`
  - `.\env\Scripts\pip install -r requirements.txt`

- Add your own .env file with Google Maps API and Telegram Bot tokens.

- Run `python main.py`.
