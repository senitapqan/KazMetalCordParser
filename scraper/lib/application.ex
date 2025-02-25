defmodule Scraper.Application do
  use Application

  def start(_type, _args) do
    children = [
      {Registry, keys: :unique, name: Scraper.Registry},
      {Oban, Application.fetch_env!(:scraper, Oban)},
      {Scraper.Repo, []}
    ]

    opts = [strategy: :one_for_one, name: Scraper.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
