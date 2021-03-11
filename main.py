if __name__ == "__main__":
    from os.path import dirname, realpath
    from scripts.Main import Main
    from scripts.getConfig import getConfig

    dir = dirname(realpath(__file__))
    Config = getConfig(dir)
    main = Main(Config)
    main.mainloop()
