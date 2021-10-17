# Unofficial Fiverr API

![Vercel](https://img.shields.io/static/v1?label=Vercel%20Build&labelColor=black&message=Success&color=ddd&logo=vercel)
![Python](https://img.shields.io/static/v1?label=Python&message=3.9.2&color=306998&logo=python&logoColor=white)
![Release](https://img.shields.io/static/v1?label=Release&message=v1.2&color=306998)

This is an unofficial api to fetch Fiverr seller's data

## How to run?

### Manually

> **Prerequisites:**  
> python >= 3.9  
> pip >= 20.3

```zsh
git clone https://github.com/salmannotkhan/fiverr-api.git
cd fiverr-api
pip3 install -r requirements.txt
uvicorn main:app
```

-   This will start localserver at `localhost:8000`

### Docker

> **Prerequirsites:**  
> Docker must be installed on system

#### Creating docker image

`docker build -t fiverr-api .`

> -t: This option will assign `fiverr-api` tag to docker image

#### Running docker container

`docker run --rm -d -p 8000:8000 fiverr-api`

> --rm: This option will delete container as soon it's stopped  
> -d: This will detach container and it will run in background  
> -p 8000:8000: This will expose container's port 8000 to host's port 8000

-   This will start server at `localhost:8000`
-   It'll also return `CONTAINER_ID` which can be used to stop container

#### Stopping docker container

`docker stop CONTAINER_ID`

## Usage

Visit API Docs from [here](https://fiverr-api.vercel.app/docs)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
