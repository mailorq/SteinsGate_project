export interface AnimeEpisode {
  number: number;
  src: string;
}

interface AnimePlayerBase {
  /** Stable identifier used for cookies. Never derive it from the visible label. */
  id: string;
  label: string;
}

export interface SingleAnimePlayer extends AnimePlayerBase {
  type: "single";
  src: string;
}

export interface EpisodeAnimePlayer extends AnimePlayerBase {
  type: "episodes";
  episodes: AnimeEpisode[];
}

export type AnimePlayer = SingleAnimePlayer | EpisodeAnimePlayer;

export interface AnimeInfo {
  slug: string;
  name: string;
  /** Короткое имя для меню «Линии» */
  menuLabel: string;
  /** Число мировой линии на divergence-метре */
  worldline: string;
  season: string;
  type: string;
  genres: string;
  description: string;
  poster: string;
  players: AnimePlayer[];
}

export const ANIMES: AnimeInfo[] = [
  {
    slug: "steins-gate",
    name: "Steins;Gate",
    menuLabel: "Steins;Gate",
    worldline: "0.337187",
    season: "2011 весна",
    type: "ТВ (25 эп.), 25 мин.",
    genres:
      "Триллер, Фантастика, Научная фантастика, Тайна, Психологический хоррор, Приключение, Романтика",
    description:
      "В Вратах Штейна рассказывается о группе молодых студентов-технарей. " +
      "Студенты находят способ менять прошлое по почте с помощью модифицированной микроволновки и начинают опыты с целью узнать, " +
      "насколько далеко сможет зайти их открытие, но в итоге все начинает выходить из-под контроля, " +
      "и студенты впутываются в заговор вокруг SERN — организации, стоящей за Большим адронным коллайдером — и Джона Титора, " +
      "утверждающего, что он явился из антиутопичного будущего.",
    poster: "/img/poster_1.webp",
    players: [
      {
        id: "episodes",
        label: "Плеер 1",
        type: "episodes",
        episodes: [
          { number: 1, src: "https://kodikplayer.com/seria/148787/4f9dc193c14cfbfc8068ffc048dadf3b/720p" },
          { number: 2, src: "https://kodikplayer.com/seria/148788/26484cae1e7f130f2dde0da9de28fa3a/720p" },
          { number: 3, src: "https://kodikplayer.com/seria/148789/083c1c017df0a7261e19928f776ee306/720p" },
          { number: 4, src: "https://kodikplayer.com/seria/148790/f0be5bb9423f45033fe03f99be82d0b8/720p" },
          { number: 5, src: "https://kodikplayer.com/seria/148791/eeb8e088f08d54731d1dfa18da3d086e/720p" },
          { number: 6, src: "https://kodikplayer.com/seria/148792/a35ab2f4e49cf10f768bae0927a28b99/720p" },
          { number: 7, src: "https://kodikplayer.com/seria/148793/b2cc43b7ae32003c754e2cb638732ce4/720p" },
          { number: 8, src: "https://kodikplayer.com/seria/148794/bc2436c091ea1a4962db61e7d045f701/720p" },
          { number: 9, src: "https://kodikplayer.com/seria/148795/55dca533c9b3a36d2f04e20fe466be4b/720p" },
          { number: 10, src: "https://kodikplayer.com/seria/148796/298815245683135d326d08942a71b746/720p" },
          { number: 11, src: "https://kodikplayer.com/seria/148797/5aac535bf0e0c195e6e1e5d04c30062c/720p" },
          { number: 12, src: "https://kodikplayer.com/seria/148798/7f860aa4b55c74a62b267431fb792ec2/720p" },
          { number: 13, src: "https://kodikplayer.com/seria/148799/8907b0541c89550dbd639e6f2b765bd3/720p" },
          { number: 14, src: "https://kodikplayer.com/seria/148800/6fc03180d1f71f4199a1aeaae9c23500/720p" },
          { number: 15, src: "https://kodikplayer.com/seria/148801/a48474b6ad234c82cd6577846b1bc8f8/720p" },
          { number: 16, src: "https://kodikplayer.com/seria/148802/ef5ed6a0c8412df79e16e6731a9e6467/720p" },
          { number: 17, src: "https://kodikplayer.com/seria/148803/2e69022f6c5c57797920dc14e5be09ae/720p" },
          { number: 18, src: "https://kodikplayer.com/seria/148804/6184293e2f8cca119046ffb9633bea07/720p" },
          { number: 19, src: "https://kodikplayer.com/seria/148805/18b4edaa4856e4de705e5ceb0a44ca53/720p" },
          { number: 20, src: "https://kodikplayer.com/seria/148806/a5900131c17849290341b6091fc125ff/720p" },
          { number: 21, src: "https://kodikplayer.com/seria/148807/3329672a35a2b425615bcff0fe533ede/720p" },
          { number: 22, src: "https://kodikplayer.com/seria/148808/f5ca6d89bfc69fb062a949220c49e78f/720p" },
          { number: 23, src: "https://kodikplayer.com/seria/148809/4c57365698c3009f0a164a4c4f91ec11/720p" },
          { number: 24, src: "https://kodikplayer.com/seria/148810/b0e925264061d9e343390ec0a2cd93a7/720p" },
        ],
      },
      {
        id: "anilibria",
        label: "Плеер 2",
        type: "single",
        src: "https://www.anilibria.tv/public/iframe.php?id=8674",
      },
    ],
  },
  {
    slug: "steins-gate-kyoukaimenjou-no-missing-link",
    name: "Steins;Gate: Kyoukaimenjou no Missing Link",
    menuLabel: "Серия 23β",
    worldline: "1.130205",
    season: "2015 зима",
    type: "24 мин.",
    genres: "Триллер, Путешествия во времени, Тайна, Психология, Романтика, Драма",
    description:
      "Специальный эпизод, включенный в Blu-ray издание Steins;Gate Complete. " +
      "Альтернативное завершение Steins;Gate, повествующее о событиях, происходивших в поле аттрактора β. " +
      "Окабe не получает послания из будущего, что подводит к началу истории Steins;Gate 0.",
    poster: "/img/poster_4.webp",
    players: [
      {
        id: "main",
        label: "Плеер 1",
        type: "single",
        src: "https://kodikplayer.com/video/86794/6ea90a51ef578ff1a7bcabee705613fc/720p?translations=false",
      },
    ],
  },
  {
    slug: "steins-gate-zero",
    name: "Steins;Gate 0",
    menuLabel: "Steins;Gate 0",
    worldline: "1.129848",
    season: "2018 весна",
    type: "ТВ (24 эп.), 25 мин.",
    genres:
      "Триллер, Фантастика, Научная фантастика, Тайна, Психологический хоррор, Психология, Романтика",
    description:
      "Альтернативная концовка Врат Штейна, " +
      "в которой эгоцентричный безумный ученый Окабе Ринтаро изо всех сил старается оправиться от неудачной попытки спасти жизнь Курису Макисе. " +
      "Стараясь забыть прошлое, Окабе отказывается от своего альтер-эго. И когда, казалось бы, всё наладилось, он снова сталкивается со своим прошлым. " +
      "Он знакомится с девушкой, которая представилась знакомой Курису. " +
      "От неё Окабе узнает, что в данный момент проходит испытание устройства, которое способно воссоздавать характер и личность человека по воспоминаниям. " +
      "Начиная тестирование он и не предполагал, что воссоздание Курису принесет столько мучений и новых неожиданных последствий...",
    poster: "/img/poster_2.webp",
    players: [
      {
        id: "episodes",
        label: "Плеер 1",
        type: "episodes",
        episodes: [
          { number: 1, src: "https://kodikplayer.com/seria/270029/8a8ccdef8597fd61ed3e66bd52eaa135/720p" },
          { number: 2, src: "https://kodikplayer.com/seria/271267/8ac5079bd55ddf58a6b32deea39370e2/720p" },
          { number: 3, src: "https://kodikplayer.com/seria/273368/671e4a5ef0479cd27fe660af70cc8f3d/720p" },
          { number: 4, src: "https://kodikplayer.com/seria/275702/4dd8b1c5c28cfe47ac8e105014af035b/720p" },
          { number: 5, src: "https://kodikplayer.com/seria/277657/22497a8f14de217885ac1a248476b959/720p" },
          { number: 6, src: "https://kodikplayer.com/seria/279620/48216b5c51e2845ef16137c757c0fbdc/720p" },
          { number: 7, src: "https://kodikplayer.com/seria/280647/01a742edf13af849bcc6c9553e74fc63/720p" },
          { number: 8, src: "https://kodikplayer.com/seria/283391/4db060c592c7c3e049f72fd9e43a9cfd/720p" },
          { number: 9, src: "https://kodikplayer.com/seria/286751/7a2ffe66090a0bf0e8be27670171ed0e/720p" },
          { number: 10, src: "https://kodikplayer.com/seria/288600/c0bd550d7c574d3304af032d1c406ce7/720p" },
          { number: 11, src: "https://kodikplayer.com/seria/290330/2e7330f7db9fbc0d20082e3e3886d2c2/720p" },
          { number: 12, src: "https://kodikplayer.com/seria/296619/85b81ddeac41dadbbd0c98faeea730e4/720p" },
          { number: 13, src: "https://kodikplayer.com/seria/303797/a061fc437670c35463695ac83405d161/720p" },
          { number: 14, src: "https://kodikplayer.com/seria/314132/eef35c79c8801afb33898b483784aa6b/720p" },
          { number: 15, src: "https://kodikplayer.com/seria/317568/c5be374d148a717971663b452be5c7bf/720p" },
          { number: 16, src: "https://kodikplayer.com/seria/319024/89e242497313c06ba07681dc7433850a/720p" },
          { number: 17, src: "https://kodikplayer.com/seria/321105/87239141da3c21bb40f34f413cdc88c5/720p" },
          { number: 18, src: "https://kodikplayer.com/seria/323107/3f5aca33df9bc638787c318d71514809/720p" },
          { number: 19, src: "https://kodikplayer.com/seria/324896/afea47ae76fb40fa75d3fb182769d6f7/720p" },
          { number: 20, src: "https://kodikplayer.com/seria/329642/f5637fdc72fc3d58bdb6b66ae894862a/720p" },
          { number: 21, src: "https://kodikplayer.com/seria/331240/72bf3503e60716119b4e7767f9dfe07b/720p" },
          { number: 22, src: "https://kodikplayer.com/seria/332795/a89e4601d7a2a779837e77a6073dad79/720p" },
          { number: 23, src: "https://kodikplayer.com/seria/335527/02549f36adb5bd78cfd265d71027c88c/720p" },
        ],
      },
      {
        id: "anilibria",
        label: "Плеер 2",
        type: "single",
        src: "https://www.anilibria.tv/public/iframe.php?id=6140",
      },
    ],
  },
  {
    slug: "steins-gate-load-region-of-deja-vu",
    name: "Steins;Gate: Load Region of Deja Vu",
    menuLabel: "Фильм",
    worldline: "1.048596",
    season: "2013 весна",
    type: "Фильм, 90 мин.",
    genres: "Триллер, Фантастика, Научная фантастика, Тайна, Психология, Романтика, Драма",
    description:
      "Сюжет фильма разворачивается спустя год после событий сериала. " +
      "Ринтаро Окабe преследуют болезненные воспоминания. " +
      "Зациклившись на созданных им временных линиях, постоянно думая о том, где он совершил ошибку и что сделал неправильно, юноша все больше и больше теряет связь с реальностью. " +
      "В итоге все эти воспоминания становятся причиной стирания его личности из пространственно-временного континуума. " +
      "Тем временем Курису Макисe возвращается в Японию после годового отсутствия. О том, что ее любимый человек действительно существовал, ей подсказывает постоянно возникающее чувство дежавю. " +
      "Этот феномен не дает ей покоя, и она изо всех сил пытается найти способ, чтобы вернуть Окабe.",
    poster: "/img/poster_3.webp",
    players: [
      {
        id: "anilibria",
        label: "Плеер 1",
        type: "single",
        src: "https://www.anilibria.tv/public/iframe.php?id=543",
      },
      {
        id: "alternate",
        label: "Плеер 2",
        type: "single",
        src: "https://kodikplayer.com/video/20557/82311913135640b736d05a065bf8194a/720p?translations=false",
      },
    ],
  },
];

export function findAnimeBySlug(slug: string | undefined): AnimeInfo | undefined {
  return ANIMES.find((anime) => anime.slug === slug);
}

export interface FaqQuestion {
  label: string;
  url: string;
}

export const FAQ_QUESTIONS: FaqQuestion[] = [
  { label: "Первоисточник", url: "https://steins-gate.fandom.com/wiki/List_of_Steins;Gate_games" },
  { label: "Мировые линии", url: "https://steins-gate.fandom.com/wiki/World_Line" },
  {
    label: "Список известных мировых линий",
    url: "https://steins-gate.fandom.com/wiki/List_of_Known_World_Lines",
  },
  { label: "СЕРН", url: "https://steins-gate.fandom.com/wiki/SERN" },
  {
    label: "Конвергенция мировых линий",
    url: "https://steins-gate.fandom.com/wiki/World_Line_Convergence",
  },
  { label: "Поля аттракторов", url: "https://steins-gate.fandom.com/wiki/Attractor_Field" },
  { label: "Считывающий Штейнер", url: "https://steins-gate.fandom.com/wiki/Reading_Steiner" },
  {
    label: "Теории перемещения во времени",
    url: "https://steins-gate.fandom.com/wiki/Time-travel_theories",
  },
  { label: "Раундеры", url: "https://steins-gate.fandom.com/wiki/Rounders" },
  { label: "Ди-мейлы", url: "https://steins-gate.fandom.com/wiki/D-Mail" },
];
