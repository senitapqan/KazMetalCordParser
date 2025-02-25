defmodule Scraper.ScrapItemWorker do
  use Oban.Worker, queue: :items, max_attempts: 10

  alias Scraper.FileWriter
  alias Scraper.Helper

  @impl Oban.Worker
  def perform(%Oban.Job{args: %{"url" => url, "path" => path}}) do
    {:ok, body} = Helper.get(url)
    {:ok, html} = Floki.parse_document(body)

    map = %{}
    [{_, _, [name]}] = Floki.find(html, "h1.producth")

    name =
      name
      |> String.split()
      |> Enum.drop(-2)
      |> Enum.join(" ")

    map = Map.put(map, "Наименование", name)
    [{_, _, elements_params}] = Floki.find(html, "ul.prodchars")

    map =
      elements_params
      |> Enum.filter(fn
        {"li", _, _} -> true
        _ -> false
      end)
      |> Enum.reduce(map, fn {_, _, [key_attrs, value_attrs]}, map ->
        {_, _, [key]} = key_attrs
        {_, _, [value]} = value_attrs
        Map.put(map, key, value)
      end)

    case Registry.lookup(Scraper.Registry, path) do
      [{pid, _}] when is_pid(pid) ->
        FileWriter.write(pid, map)
      _ ->
        IO.puts("❌ No active FileWriter found for path #{path}")
    end
    :ok
  end
end
