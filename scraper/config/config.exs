import Config

config :logger, level: :debug

config :scraper,
  ecto_repos: [Scraper.Repo]

config :scraper, Oban,
  repo: Scraper.Repo,
  queues: [items: 20, pages: 10, tables: 10],
  insert_trigger: false

config :scraper, Scraper.Repo,
  username: "postgres",
  password: "senitapqan",
  hostname: "localhost",
  port: 1111,
  database: "postgres",
  stacktrace: true,
  show_sensitive_data_on_connection_error: true,
  pool_size: 10
