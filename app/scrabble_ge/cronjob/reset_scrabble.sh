
source ./.env

wget --header="Authorization: bearer ${ACCESS_TOKEN}" "http://${SRV_ADDRESS}:${SRV_PORT}/word_game/reset" -O /dev/null || touch error.log