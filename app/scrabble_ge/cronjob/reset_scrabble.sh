
source ./.env

wget --header="Authorization: bearer ${ACCESS_TOKEN}" "https://${SRV_ADDRESS}/word_game/reset" -O /dev/null || touch error.log