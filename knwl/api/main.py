def main():
    import uvicorn

    uvicorn.run(
        "knwl.api.knwl_api.main:app", host="0.0.0.0", port=10000, reload=True, workers=1
    )  # note that FastAPI reload only works with 1 worker


if __name__ == "__main__":
    main()
